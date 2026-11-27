"""
Label Errors detection module for Data Detective (Classification only).
Computes out-of-fold predicted probabilities using cross-validation with LogisticRegression
and RandomForest, utilizes Cleanlab's find_label_issues, and implements a robust fallback
margin detector to produce a prioritized review queue.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold, StratifiedKFold, cross_val_predict

logger = logging.getLogger("data_detective.label_errors")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s [%(name)s]: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def detect_label_errors(
    df: pd.DataFrame,
    target_col: str,
    target_type: str,
    preprocessed_X: np.ndarray,
    encoded_y: np.ndarray,
    target_encoder: Optional[Any] = None,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Audits classification labels for potential errors, generating a prioritized review queue.
    """
    results: Dict[str, Any] = {
        "review_queue": [],
        "total_issues_found": 0,
        "cleanlab_issues_count": 0,
        "fallback_issues_count": 0,
        "summary": {
            "total_candidates": 0,
            "avg_confidence_on_errors": 0.0,
            "severity": "Clean",
            "message": "",
        },
    }

    if target_type != "classification":
        results["summary"]["message"] = "Label error audit only applies to classification tasks."
        return results

    if df.empty or encoded_y is None or len(encoded_y) == 0:
        results["summary"]["message"] = "No target labels provided."
        return results

    n_samples = len(df)
    unique_classes, class_counts = np.unique(encoded_y, return_counts=True)
    n_classes = len(unique_classes)

    # Edge Case: Single-class dataset
    if n_classes < 2:
        results["summary"]["message"] = (
            f"Dataset has only {n_classes} target class. At least 2 classes are required."
        )
        return results

    # Edge Case: Insufficient rows
    if n_samples < 6:
        results["summary"]["message"] = (
            f"Dataset has only {n_samples} rows. Need at least 6 rows for cross-validated label audit."
        )
        return results

    min_class_size = int(np.min(class_counts))
    # Determine safe number of folds
    if min_class_size >= 5 and n_samples >= 25:
        n_splits = 5
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    elif min_class_size >= 2 and n_samples >= 10:
        n_splits = min(3, min_class_size)
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    else:
        # Extreme imbalance: fallback to standard KFold
        n_splits = min(3, max(2, n_samples // 3))
        cv = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)

    logger.info(
        "Computing OOF probabilities across %d classes with %d-fold CV...", n_classes, n_splits
    )

    # 1. Out-Of-Fold probabilities with Logistic Regression
    oof_lr: Optional[np.ndarray] = None
    try:
        lr_model = LogisticRegression(
            max_iter=1000,
            C=1.0,
            random_state=random_state,
        )
        oof_lr = cross_val_predict(
            lr_model, preprocessed_X, encoded_y, cv=cv, method="predict_proba"
        )
    except Exception as e:
        logger.warning("Logistic Regression OOF prediction failed: %s", e)

    # 2. Out-Of-Fold probabilities with Random Forest
    oof_rf: Optional[np.ndarray] = None
    try:
        rf_model = RandomForestClassifier(
            n_estimators=50,
            max_depth=6,
            min_samples_split=max(2, min_class_size // 2),
            random_state=random_state,
        )
        oof_rf = cross_val_predict(
            rf_model, preprocessed_X, encoded_y, cv=cv, method="predict_proba"
        )
    except Exception as e:
        logger.warning("Random Forest OOF prediction failed: %s", e)

    # Ensemble / Average Probabilities
    if oof_lr is not None and oof_rf is not None:
        oof_probs = (oof_lr + oof_rf) / 2.0
    elif oof_rf is not None:
        oof_probs = oof_rf
    elif oof_lr is not None:
        oof_probs = oof_lr
    else:
        results["summary"]["message"] = "Both classification models failed to produce OOF predictions."
        return results

    # Normalize row probabilities to sum to 1.0
    row_sums = oof_probs.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    oof_probs = oof_probs / row_sums

    # 3. Cleanlab Detection
    cleanlab_issue_indices = set()
    cleanlab_quality_scores = {}
    try:
        import cleanlab
        from cleanlab.filter import find_label_issues
        from cleanlab.rank import get_label_quality_scores

        quality_scores = get_label_quality_scores(
            labels=encoded_y,
            pred_probs=oof_probs,
        )
        for idx, score in enumerate(quality_scores):
            cleanlab_quality_scores[idx] = float(score)

        issue_mask = find_label_issues(
            labels=encoded_y,
            pred_probs=oof_probs,
            filter_by="self_confidence",
        )
        if isinstance(issue_mask, np.ndarray) and issue_mask.dtype == bool:
            cleanlab_issue_indices = set(int(i) for i in np.where(issue_mask)[0])
        elif isinstance(issue_mask, (list, np.ndarray)):
            cleanlab_issue_indices = set(int(i) for i in issue_mask)
        results["cleanlab_issues_count"] = len(cleanlab_issue_indices)
        logger.info("Cleanlab flagged %d potential label issues.", len(cleanlab_issue_indices))
    except Exception as e:
        logger.debug("Cleanlab execution note: %s", e)

    # 4. Fallback Detection: Margin & Confidence Analysis
    fallback_issue_indices = set()
    for i in range(n_samples):
        given_lbl = encoded_y[i]
        probs = oof_probs[i]
        predicted_lbl = int(np.argmax(probs))
        pred_conf = float(probs[predicted_lbl])
        given_conf = float(probs[given_lbl])

        # Flag if model predicts different class with strong confidence and given class probability is depressed
        if predicted_lbl != given_lbl:
            if pred_conf > 0.55 and given_conf < 0.35:
                fallback_issue_indices.add(i)

    results["fallback_issues_count"] = len(fallback_issue_indices)

    # Combine detections
    all_candidate_indices = sorted(list(cleanlab_issue_indices | fallback_issue_indices))
    results["total_issues_found"] = len(all_candidate_indices)

    # Label class decoding mapping
    class_map = {}
    if target_encoder and hasattr(target_encoder, "classes_"):
        class_map = {idx: str(cls) for idx, cls in enumerate(target_encoder.classes_)}
    else:
        class_map = {idx: str(idx) for idx in range(n_classes)}

    # Build review queue
    review_queue = []
    for idx in all_candidate_indices:
        orig_row_idx = df.index[idx]
        given_int = encoded_y[idx]
        pred_int = int(np.argmax(oof_probs[idx]))

        given_label_str = class_map.get(given_int, str(given_int))
        pred_label_str = class_map.get(pred_int, str(pred_int))

        pred_confidence = float(oof_probs[idx][pred_int])
        given_confidence = float(oof_probs[idx][given_int])

        # Quality score (lower means worse label quality)
        label_quality = cleanlab_quality_scores.get(
            idx, round(max(0.0, 1.0 - (pred_confidence - given_confidence)), 3)
        )

        # Model agreement
        lr_pred = int(np.argmax(oof_lr[idx])) if oof_lr is not None else None
        rf_pred = int(np.argmax(oof_rf[idx])) if oof_rf is not None else None
        models_agree = (lr_pred == rf_pred) if (lr_pred is not None and rf_pred is not None) else True

        detected_by = []
        if idx in cleanlab_issue_indices:
            detected_by.append("Cleanlab Self-Confidence")
        if idx in fallback_issue_indices:
            detected_by.append("Margin Fallback")

        # Severity
        if pred_confidence > 0.85 and models_agree:
            severity = "High"
        elif pred_confidence > 0.65:
            severity = "Medium"
        else:
            severity = "Low"

        review_queue.append(
            {
                "row_index": int(orig_row_idx),
                "position": int(idx),
                "given_label": given_label_str,
                "suggested_label": pred_label_str,
                "model_confidence": round(pred_confidence, 3),
                "given_label_confidence": round(given_confidence, 3),
                "label_quality_score": round(label_quality, 3),
                "models_agree": bool(models_agree),
                "detected_by": ", ".join(detected_by),
                "severity": severity,
                "status": "Needs Human Review",
            }
        )

    # Sort queue ascending by label_quality_score (lowest quality first)
    review_queue.sort(key=lambda x: x["label_quality_score"])
    results["review_queue"] = review_queue

    total_candidates = len(review_queue)
    results["summary"]["total_candidates"] = total_candidates

    if total_candidates > 0:
        avg_conf = float(np.mean([item["model_confidence"] for item in review_queue]))
        results["summary"]["avg_confidence_on_errors"] = round(avg_conf, 3)

        high_sev = sum(1 for item in review_queue if item["severity"] == "High")
        if high_sev > 0 or total_candidates > 0.05 * n_samples:
            results["summary"]["severity"] = "High"
        elif total_candidates > 0:
            results["summary"]["severity"] = "Medium"
        else:
            results["summary"]["severity"] = "Low"
    else:
        results["summary"]["severity"] = "Clean"
        results["summary"]["message"] = "No obvious label issues identified by OOF cross-validation."

    logger.info(
        "Label audit complete: %d candidate errors queued. Severity: %s",
        total_candidates,
        results["summary"]["severity"],
    )

    return results
