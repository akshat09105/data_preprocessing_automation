"""Unit tests for detective.anomalies module."""

import numpy as np
import pandas as pd
import pytest

from detective.anomalies import detect_anomalies
from detective.preprocess import PreprocessPipeline


def test_detect_anomalies_with_attribution():
    np.random.seed(42)
    n = 100
    # Clean normal distribution
    X_clean = np.random.normal(loc=0.0, scale=1.0, size=(n, 4))
    df = pd.DataFrame(X_clean, columns=["feat0", "feat1", "feat2", "feat3"])

    # Inject extreme anomaly at index 12 in feat2 (+10 std deviations)
    df.loc[12, "feat2"] = 10.0

    pipeline = PreprocessPipeline()
    X_trans, _, _ = pipeline.fit_transform(df)

    results = detect_anomalies(
        df=df,
        preprocessed_X=X_trans,
        feature_names=pipeline.feature_names_,
        contamination=0.05,
        random_state=42,
    )

    assert results["total_anomalies"] > 0
    top_anomaly = results["ranked_anomalies"][0]
    # Check that row 12 is at or near the top
    assert 12 in results["anomaly_indices"][:3]

    # Verify feature attribution identified feat2
    row_12_record = next(r for r in results["ranked_anomalies"] if r["row_index"] == 12)
    top_attrib = row_12_record["top_features"][0]["feature"]
    assert "feat2" in top_attrib
    assert abs(row_12_record["top_features"][0]["z_score"]) > 3.0
