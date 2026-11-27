"""
Anomaly detection module for Data Detective.
Combines Isolation Forest, PCA Reconstruction Error, and Local Outlier Factor (LOF)
into a normalized [0, 1] anomaly score. Provides feature-level attribution
(z-scores & reconstruction errors) explaining WHY a row is unusual.
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor

logger = logging.getLogger("data_detective.anomalies")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s [%(name)s]: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def _min_max_scale(arr: np.ndarray) -> np.ndarray:
    """Scale 1D array to [0, 1] range safely."""
    min_val = np.nanmin(arr)
    max_val = np.nanmax(arr)
    if max_val - min_val > 1e-9:
        return (arr - min_val) / (max_val - min_val)
    return np.zeros_like(arr)


def detect_anomalies(
    df: pd.DataFrame,
    preprocessed_X: np.ndarray,
    feature_names: Optional[List[str]] = None,
    contamination: float = 0.05,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Identifies anomalous samples using multi-signal classical algorithms
    and produces a ranked queue with feature-level explanation.
    """
    results: Dict[str, Any] = {
        "ranked_anomalies": [],
        "anomaly_indices": [],
        "all_scores": [],
        "total_anomalies": 0,
        "contamination": contamination,
        "threshold": 0.5,
        "summary": {
            "total_flagged": 0,
            "avg_score_flagged": 0.0,
            "severity": "Clean",
            "advisory": (
                "Anomalies represent statistically rare patterns or combinations. "
                "They are candidates for review, but may represent valid rare events."
            ),
        },
    }

    n_samples = len(df)
    if n_samples < 5 or preprocessed_X is None or preprocessed_X.shape[1] == 0:
        logger.warning("Insufficient samples or features for anomaly detection.")
        return results

    n_features = preprocessed_X.shape[1]
    feature_names = feature_names or [f"feature_{i}" for i in range(n_features)]

    # 1. Isolation Forest
    iso_scores = np.zeros(n_samples)
    try:
        iso = IsolationForest(
            contamination=max(0.01, min(0.25, contamination)),
            random_state=random_state,
            n_estimators=100,
        )
        iso.fit(preprocessed_X)
        # score_samples returns opposite of anomaly score (lower is more anomalous)
        raw_iso = -iso.score_samples(preprocessed_X)
        iso_scores = _min_max_scale(raw_iso)
    except Exception as e:
        logger.warning("IsolationForest failed: %s", e)

    # 2. PCA Reconstruction Error
    pca_scores = np.zeros(n_samples)
    pca_residuals = np.zeros_like(preprocessed_X)
    try:
        n_components = max(1, min(n_features - 1, int(np.sqrt(n_features)) + 1, n_samples - 1))
        pca = PCA(n_components=n_components, random_state=random_state)
        X_reduced = pca.fit_transform(preprocessed_X)
        X_reconstructed = pca.inverse_transform(X_reduced)
        pca_residuals = np.abs(preprocessed_X - X_reconstructed)
        raw_recon = np.linalg.norm(pca_residuals, axis=1)
        pca_scores = _min_max_scale(raw_recon)
    except Exception as e:
        logger.warning("PCA reconstruction calculation failed: %s", e)

    # 3. Local Outlier Factor
    lof_scores = np.zeros(n_samples)
    try:
        n_neighbors = max(3, min(20, n_samples - 1))
        lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
        lof.fit(preprocessed_X)
        raw_lof = -lof.negative_outlier_factor_
        lof_scores = _min_max_scale(raw_lof)
    except Exception as e:
        logger.warning("LOF failed: %s", e)

    # Ensemble Weighted Score
    # IsolationForest: 0.50, PCA: 0.30, LOF: 0.20
    composite_scores = 0.50 * iso_scores + 0.30 * pca_scores + 0.20 * lof_scores
    composite_scores = _min_max_scale(composite_scores)
    results["all_scores"] = [round(float(s), 4) for s in composite_scores]

    # Threshold determination: based on contamination percentile or fixed cutoff
    cutoff_percentile = (1.0 - contamination) * 100.0
    threshold = float(np.percentile(composite_scores, cutoff_percentile))
    threshold = max(threshold, 0.45)  # Enforce minimum anomaly barrier
    results["threshold"] = round(threshold, 3)

    # Calculate standard z-scores on preprocessed features for explainability
    mean_vec = np.mean(preprocessed_X, axis=0)
    std_vec = np.std(preprocessed_X, axis=0)
    std_vec[std_vec == 0] = 1.0
    z_scores = (preprocessed_X - mean_vec) / std_vec

    ranked_list = []
    # Identify flagged rows
    flagged_mask = composite_scores >= threshold
    flagged_indices = np.where(flagged_mask)[0]

    # If few flagged by threshold, always review top candidates up to contamination rate
    if len(flagged_indices) == 0:
        top_k = max(1, int(np.ceil(contamination * n_samples)))
        flagged_indices = np.argsort(composite_scores)[-top_k:]

    for idx in flagged_indices:
        score = float(composite_scores[idx])
        orig_row_idx = df.index[idx]

        # Find top 3 contributing features
        # Combined z-score magnitude and PCA residual
        feat_deviation = np.abs(z_scores[idx]) + 0.5 * pca_residuals[idx]
        top_feat_indices = np.argsort(feat_deviation)[::-1][:3]

        top_contributions = []
        for f_idx in top_feat_indices:
            feat_name = feature_names[f_idx]
            z_val = float(z_scores[idx, f_idx])
            raw_val = None
            # Check if this feature is a raw column in original dataframe
            for raw_col in df.columns:
                if raw_col == feat_name or feat_name.endswith(raw_col):
                    raw_val = str(df.loc[orig_row_idx, raw_col])
                    break

            top_contributions.append(
                {
                    "feature": feat_name,
                    "z_score": round(z_val, 2),
                    "raw_value": raw_val,
                    "explanation": f"{abs(z_val):.1f} std deviations from average",
                }
            )

        # Severity
        if score > 0.80:
            severity = "High"
        elif score > 0.60:
            severity = "Medium"
        else:
            severity = "Low"

        ranked_list.append(
            {
                "row_index": int(orig_row_idx),
                "position": int(idx),
                "anomaly_score": round(score, 3),
                "iso_forest_score": round(float(iso_scores[idx]), 3),
                "pca_score": round(float(pca_scores[idx]), 3),
                "lof_score": round(float(lof_scores[idx]), 3),
                "severity": severity,
                "top_features": top_contributions,
                "primary_reason": (
                    f"Extreme deviation in {top_contributions[0]['feature']} "
                    f"({top_contributions[0]['explanation']})"
                    if top_contributions
                    else "High multidimensional isolation"
                ),
                "status": "Candidate Rare Event / Anomaly",
            }
        )

    # Sort descending by anomaly score
    ranked_list.sort(key=lambda x: x["anomaly_score"], reverse=True)
    results["ranked_anomalies"] = ranked_list
    results["anomaly_indices"] = [r["row_index"] for r in ranked_list]
    results["total_anomalies"] = len(ranked_list)
    results["summary"]["total_flagged"] = len(ranked_list)

    if ranked_list:
        results["summary"]["avg_score_flagged"] = round(
            float(np.mean([r["anomaly_score"] for r in ranked_list])), 3
        )
        high_count = sum(1 for r in ranked_list if r["severity"] == "High")
        if high_count > 0:
            results["summary"]["severity"] = "High"
        else:
            results["summary"]["severity"] = "Medium"
    else:
        results["summary"]["severity"] = "Clean"

    logger.info(
        "Anomaly detection complete: %d anomalies flagged (Severity: %s, Threshold: %.3f)",
        len(ranked_list),
        results["summary"]["severity"],
        results["threshold"],
    )

    return results
