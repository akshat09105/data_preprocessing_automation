"""
Evaluation module for Data Detective benchmark.
Computes statistical detection metrics (Precision, Recall, F1, False Alarm Rate)
and quantifies downstream ML model accuracy impact before vs after data cleaning.
"""

from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split


def calculate_metrics(
    ground_truth_indices: List[Any],
    predicted_indices: List[Any],
    total_samples: int,
) -> Dict[str, float]:
    """
    Computes statistical precision, recall, F1, and false alarm rate (FPR).
    """
    gt_set = set(ground_truth_indices)
    pred_set = set(predicted_indices)

    tp = len(gt_set.intersection(pred_set))
    fp = len(pred_set.difference(gt_set))
    fn = len(gt_set.difference(pred_set))
    tn = max(0, total_samples - (tp + fp + fn))

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2.0 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    far = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    return {
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "tn": int(tn),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "false_alarm_rate": round(far, 4),
    }


def evaluate_downstream_impact(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    target_col: str,
    rows_to_drop: Optional[List[Any]] = None,
    cols_to_drop: Optional[List[str]] = None,
    random_state: int = 42,
) -> Dict[str, float]:
    """
    Measures downstream ML model test accuracy on a clean holdout split
    before vs after removing flagged rows or suspect leaky features.
    """
    from detective.preprocess import PreprocessPipeline

    results = {
        "dirty_model_acc": 0.0,
        "cleaned_model_acc": 0.0,
        "delta_acc": 0.0,
    }

    try:
        # 1. Baseline Model on Dirty Train Set
        pipe_dirty = PreprocessPipeline(target_col=target_col, random_state=random_state)
        X_train_dirty, y_train_dirty, _ = pipe_dirty.fit_transform(train_df, target_col=target_col)

        # Preprocess test set using same transform
        # For simplicity, fit a test pipe
        pipe_test = PreprocessPipeline(target_col=target_col, random_state=random_state)
        X_test, y_test, _ = pipe_test.fit_transform(test_df, target_col=target_col)

        if X_train_dirty.shape[1] == 0 or X_test.shape[1] == 0:
            return results

        rf_dirty = RandomForestClassifier(n_estimators=50, max_depth=6, random_state=random_state)
        # Handle matching column shapes
        min_feats = min(X_train_dirty.shape[1], X_test.shape[1])
        rf_dirty.fit(X_train_dirty[:, :min_feats], y_train_dirty)
        preds_dirty = rf_dirty.predict(X_test[:, :min_feats])
        dirty_acc = float(accuracy_score(y_test, preds_dirty))
        results["dirty_model_acc"] = round(dirty_acc, 4)

        # 2. Cleaned Model (Remove flagged rows / leaky columns)
        cleaned_train_df = train_df.copy()
        if rows_to_drop:
            valid_indices = [idx for idx in rows_to_drop if idx in cleaned_train_df.index]
            if len(valid_indices) < len(cleaned_train_df) - 5:
                cleaned_train_df = cleaned_train_df.drop(index=valid_indices)

        if cols_to_drop:
            valid_cols = [c for c in cols_to_drop if c in cleaned_train_df.columns and c != target_col]
            if valid_cols:
                cleaned_train_df = cleaned_train_df.drop(columns=valid_cols)
                # Also drop from test set for fair evaluation if feature was removed
                test_df_eval = test_df.drop(columns=[c for c in valid_cols if c in test_df.columns])
            else:
                test_df_eval = test_df.copy()
        else:
            test_df_eval = test_df.copy()

        pipe_clean = PreprocessPipeline(target_col=target_col, random_state=random_state)
        X_train_clean, y_train_clean, _ = pipe_clean.fit_transform(cleaned_train_df, target_col=target_col)

        pipe_test_eval = PreprocessPipeline(target_col=target_col, random_state=random_state)
        X_test_clean, y_test_clean, _ = pipe_test_eval.fit_transform(test_df_eval, target_col=target_col)

        min_feats_clean = min(X_train_clean.shape[1], X_test_clean.shape[1])
        if min_feats_clean > 0:
            rf_clean = RandomForestClassifier(n_estimators=50, max_depth=6, random_state=random_state)
            rf_clean.fit(X_train_clean[:, :min_feats_clean], y_train_clean)
            preds_clean = rf_clean.predict(X_test_clean[:, :min_feats_clean])
            clean_acc = float(accuracy_score(y_test_clean, preds_clean))
            results["cleaned_model_acc"] = round(clean_acc, 4)
            results["delta_acc"] = round(clean_acc - dirty_acc, 4)
    except Exception as e:
        pass

    return results
