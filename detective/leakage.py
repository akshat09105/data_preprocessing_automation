"""
Target Leakage detection module for Data Detective.
Combines 5 complementary mathematical & heuristic checks to detect potential
target leakage, assigning suspicion scores, confidence levels, and evidence.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
from sklearn.inspection import permutation_importance
from sklearn.metrics import accuracy_score, r2_score
from sklearn.model_selection import KFold, StratifiedKFold, cross_val_score
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

logger = logging.getLogger("data_detective.leakage")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s [%(name)s]: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

NAME_HEURISTIC_KEYWORDS = [
    "target",
    "label",
    "outcome",
    "final",
    "status",
    "result",
    "groundtruth",
    "ground_truth",
    "y_val",
    "y_true",
    "class",
    "dependent",
]


def detect_leakage(
    df: pd.DataFrame,
    target_col: str,
    target_type: str = "classification",
    preprocessed_X: Optional[np.ndarray] = None,
    encoded_y: Optional[np.ndarray] = None,
    feature_names: Optional[List[str]] = None,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Audits features for target leakage using multi-evidence statistical testing.
    """
    results: Dict[str, Any] = {
        "suspect_features": [],
        "feature_metrics": {},
        "summary": {
            "total_suspects": 0,
            "high_confidence_count": 0,
            "medium_confidence_count": 0,
            "low_confidence_count": 0,
            "severity": "Clean",
        },
    }

    if df.empty or target_col not in df.columns:
        return results

    raw_feature_cols = [c for c in df.columns if c != target_col]
    if not raw_feature_cols:
        return results

    n_samples = len(df)
    if n_samples < 10:
        logger.warning("Dataset too small for reliable leakage detection (<10 samples).")
        return results

    # Determine CV strategy
    cv_splits = min(3, max(2, n_samples // 5))

    # Pre-calculate baseline model score on all features if preprocessed X is available
    baseline_score = 0.0
    if preprocessed_X is not None and encoded_y is not None and preprocessed_X.shape[1] > 0:
        try:
            if target_type == "classification":
                # Ensure stratified kfold is possible
                unique_y, y_counts = np.unique(encoded_y, return_counts=True)
                if len(unique_y) > 1 and np.min(y_counts) >= cv_splits:
                    cv = StratifiedKFold(n_splits=cv_splits, shuffle=True, random_state=random_state)
                else:
                    cv = KFold(n_splits=cv_splits, shuffle=True, random_state=random_state)
                clf = RandomForestClassifier(n_estimators=30, max_depth=5, random_state=random_state)
                scores = cross_val_score(clf, preprocessed_X, encoded_y, cv=cv, scoring="accuracy")
                baseline_score = float(np.mean(scores))
            else:
                cv = KFold(n_splits=cv_splits, shuffle=True, random_state=random_state)
                reg = RandomForestRegressor(n_estimators=30, max_depth=5, random_state=random_state)
                scores = cross_val_score(reg, preprocessed_X, encoded_y, cv=cv, scoring="r2")
                baseline_score = float(np.mean(scores))
        except Exception as e:
            logger.warning("Baseline model training failed: %s", e)

    # Global permutation importance on full preprocessed features if feasible
    feature_imp_map: Dict[str, float] = {}
    if (
        preprocessed_X is not None
        and encoded_y is not None
        and preprocessed_X.shape[1] > 1
        and preprocessed_X.shape[1] <= 100
    ):
        try:
            if target_type == "classification":
                rf = RandomForestClassifier(n_estimators=35, max_depth=6, random_state=random_state)
            else:
                rf = RandomForestRegressor(n_estimators=35, max_depth=6, random_state=random_state)
            rf.fit(preprocessed_X, encoded_y)
            perm = permutation_importance(
                rf, preprocessed_X, encoded_y, n_repeats=3, random_state=random_state, n_jobs=1
            )
            raw_imps = np.maximum(0, perm.importances_mean)
            total_imp = np.sum(raw_imps)
            if total_imp > 0:
                norm_imps = raw_imps / total_imp
                if feature_names and len(feature_names) == len(norm_imps):
                    for fname, imp in zip(feature_names, norm_imps):
                        feature_imp_map[fname] = float(imp)
        except Exception as e:
            logger.warning("Permutation importance calculation skipped: %s", e)

    target_series = df[target_col]

    # Evaluate each raw column
    for col in raw_feature_cols:
        col_series = df[col]
        evidence_list: List[str] = []
        checks_passed = 0
        score_components = []

        # Check 1: Target copy / near-copy
        is_exact = False
        try:
            if col_series.equals(target_series):
                is_exact = True
                evidence_list.append("Exact 100% copy of the target column.")
                checks_passed += 3  # Immediate strong weight
                score_components.append(1.0)
            elif col_series.dropna().nunique() > 1 and target_series.dropna().nunique() > 1:
                # Numeric or categorical correlation
                if pd.api.types.is_numeric_dtype(col_series) and pd.api.types.is_numeric_dtype(target_series):
                    valid_mask = col_series.notna() & target_series.notna()
                    if valid_mask.sum() > 5:
                        corr = float(np.corrcoef(col_series[valid_mask], target_series[valid_mask])[0, 1])
                        abs_corr = abs(corr) if not np.isnan(corr) else 0.0
                        if abs_corr > 0.98:
                            evidence_list.append(f"Near-perfect linear correlation with target (r = {corr:.3f}).")
                            checks_passed += 2
                            score_components.append(0.95)
                        elif abs_corr > 0.90:
                            evidence_list.append(f"Very high linear correlation with target (r = {corr:.3f}).")
                            checks_passed += 1
                            score_components.append(0.70)
        except Exception as e:
            logger.debug("Correlation check failed for %s: %s", col, e)

        # Check 2: Single-feature predictive power with shallow Decision Tree
        single_feat_score = 0.0
        try:
            # Prepare single feature
            if pd.api.types.is_numeric_dtype(col_series):
                feat_vals = col_series.fillna(col_series.median()).values.reshape(-1, 1)
            else:
                cat_codes = pd.Categorical(col_series.astype(str)).codes.reshape(-1, 1)
                feat_vals = cat_codes

            if target_type == "classification" and encoded_y is not None:
                unique_y, y_counts = np.unique(encoded_y, return_counts=True)
                if len(unique_y) > 1 and np.min(y_counts) >= cv_splits:
                    cv = StratifiedKFold(n_splits=cv_splits, shuffle=True, random_state=random_state)
                else:
                    cv = KFold(n_splits=cv_splits, shuffle=True, random_state=random_state)
                dt = DecisionTreeClassifier(max_depth=2, random_state=random_state)
                s_scores = cross_val_score(dt, feat_vals, encoded_y, cv=cv, scoring="accuracy")
                single_feat_score = float(np.mean(s_scores))

                # Check if unrealistically high compared to baseline/majority
                majority_pct = float(np.max(y_counts) / len(encoded_y))
                if single_feat_score > 0.95 and single_feat_score > (majority_pct + 0.15):
                    evidence_list.append(
                        f"Single-feature decision tree achieves {single_feat_score*100:.1f}% accuracy alone."
                    )
                    checks_passed += 2
                    score_components.append(0.90)
                elif single_feat_score > 0.88 and single_feat_score > (majority_pct + 0.20):
                    evidence_list.append(
                        f"Unusually high single-feature predictive power ({single_feat_score*100:.1f}% CV accuracy)."
                    )
                    checks_passed += 1
                    score_components.append(0.65)
            elif target_type == "regression" and encoded_y is not None:
                cv = KFold(n_splits=cv_splits, shuffle=True, random_state=random_state)
                dt = DecisionTreeRegressor(max_depth=2, random_state=random_state)
                s_scores = cross_val_score(dt, feat_vals, encoded_y, cv=cv, scoring="r2")
                single_feat_score = float(np.mean(s_scores))
                if single_feat_score > 0.95:
                    evidence_list.append(
                        f"Single-feature decision tree achieves R² = {single_feat_score:.3f} alone."
                    )
                    checks_passed += 2
                    score_components.append(0.90)
                elif single_feat_score > 0.80:
                    evidence_list.append(
                        f"Strong single-feature regression power (R² = {single_feat_score:.3f})."
                    )
                    checks_passed += 1
                    score_components.append(0.60)
        except Exception as e:
            logger.debug("Single feature DT failed for %s: %s", col, e)

        # Check 3: Permutation Importance dominance
        # Sum importance for one-hot encoded dummy columns belonging to this raw column
        col_total_imp = 0.0
        for fname, imp in feature_imp_map.items():
            if fname.endswith(col) or f"__{col}_" in fname or fname == col:
                col_total_imp += imp
        if col_total_imp > 0.55:
            evidence_list.append(
                f"Feature dominates overall model with {col_total_imp*100:.1f}% of total permutation importance."
            )
            checks_passed += 1
            score_components.append(0.70)

        # Check 4: Score Drop Delta
        # If removing this feature causes the model performance to collapse drastically
        score_drop_delta = 0.0
        if (
            preprocessed_X is not None
            and encoded_y is not None
            and preprocessed_X.shape[1] > 2
            and baseline_score > 0.6
        ):
            try:
                # Find indices corresponding to this column
                indices_to_drop = [
                    i
                    for i, fname in enumerate(feature_names or [])
                    if fname.endswith(col) or f"__{col}_" in fname or fname == col
                ]
                if indices_to_drop and len(indices_to_drop) < preprocessed_X.shape[1]:
                    reduced_X = np.delete(preprocessed_X, indices_to_drop, axis=1)
                    if target_type == "classification":
                        clf_reduced = RandomForestClassifier(
                            n_estimators=30, max_depth=5, random_state=random_state
                        )
                        r_scores = cross_val_score(
                            clf_reduced, reduced_X, encoded_y, cv=cv, scoring="accuracy"
                        )
                        reduced_score = float(np.mean(r_scores))
                    else:
                        reg_reduced = RandomForestRegressor(
                            n_estimators=30, max_depth=5, random_state=random_state
                        )
                        r_scores = cross_val_score(
                            reg_reduced, reduced_X, encoded_y, cv=cv, scoring="r2"
                        )
                        reduced_score = float(np.mean(r_scores))

                    score_drop_delta = baseline_score - reduced_score
                    if score_drop_delta > 0.20:
                        evidence_list.append(
                            f"Model score drops by {score_drop_delta:.3f} when this feature is excluded."
                        )
                        checks_passed += 1
                        score_components.append(0.75)
            except Exception as e:
                logger.debug("Score drop check failed for %s: %s", col, e)

        # Check 5: Name-based heuristics (low weight)
        col_lower = str(col).lower()
        has_name_keyword = any(kw in col_lower for kw in NAME_HEURISTIC_KEYWORDS)
        if has_name_keyword:
            evidence_list.append(f"Column name contains target-associated term ('{col}').")
            score_components.append(0.20)
            if checks_passed > 0:
                checks_passed += 1

        # Synthesize Suspicion Score and Confidence
        if is_exact:
            suspicion_score = 1.0
            confidence = "High"
        elif score_components:
            # Weighted average favoring the maximum individual signal
            max_comp = max(score_components)
            mean_comp = sum(score_components) / len(score_components)
            suspicion_score = round(min(1.0, 0.7 * max_comp + 0.3 * mean_comp), 3)

            if checks_passed >= 3 or suspicion_score >= 0.85:
                confidence = "High"
            elif checks_passed == 2 or suspicion_score >= 0.65:
                confidence = "Medium"
            elif checks_passed >= 1 or suspicion_score >= 0.40:
                confidence = "Low"
            else:
                confidence = "Clean"
        else:
            suspicion_score = 0.0
            confidence = "Clean"

        feature_record = {
            "feature": col,
            "suspicion_score": suspicion_score,
            "confidence": confidence,
            "single_feature_score": round(single_feat_score, 3),
            "permutation_importance": round(col_total_imp, 3),
            "score_drop_delta": round(score_drop_delta, 3),
            "evidence": evidence_list,
            "recommendation": (
                "High probability of post-outcome leakage. Review whether this variable is available at inference time."
                if confidence == "High"
                else "Moderate suspicion. Verify timing and data collection process."
                if confidence == "Medium"
                else "Weak signal. Verify feature definition."
                if confidence == "Low"
                else "Feature appears clean."
            ),
        }

        results["feature_metrics"][col] = feature_record
        if confidence in ["High", "Medium", "Low"]:
            results["suspect_features"].append(feature_record)

    # Sort suspects descending by suspicion score
    results["suspect_features"].sort(key=lambda x: x["suspicion_score"], reverse=True)

    high_count = sum(1 for f in results["suspect_features"] if f["confidence"] == "High")
    med_count = sum(1 for f in results["suspect_features"] if f["confidence"] == "Medium")
    low_count = sum(1 for f in results["suspect_features"] if f["confidence"] == "Low")

    results["summary"]["total_suspects"] = len(results["suspect_features"])
    results["summary"]["high_confidence_count"] = high_count
    results["summary"]["medium_confidence_count"] = med_count
    results["summary"]["low_confidence_count"] = low_count

    if high_count > 0:
        results["summary"]["severity"] = "High"
    elif med_count > 0:
        results["summary"]["severity"] = "Medium"
    elif low_count > 0:
        results["summary"]["severity"] = "Low"
    else:
        results["summary"]["severity"] = "Clean"

    logger.info(
        "Leakage audit complete: %d suspects (High: %d, Medium: %d, Low: %d)",
        len(results["suspect_features"]),
        high_count,
        med_count,
        low_count,
    )

    return results
