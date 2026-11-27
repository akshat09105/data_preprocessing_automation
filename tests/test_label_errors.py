"""Unit tests for detective.label_errors module."""

import numpy as np
import pandas as pd
import pytest

from detective.label_errors import detect_label_errors
from detective.preprocess import PreprocessPipeline


def test_detect_label_errors():
    np.random.seed(42)
    n = 100
    # Create two well-separated clusters
    c1 = np.random.normal(loc=[-2.0, -2.0], scale=0.5, size=(50, 2))
    c2 = np.random.normal(loc=[2.0, 2.0], scale=0.5, size=(50, 2))

    X_data = np.vstack([c1, c2])
    y_true = np.array([0] * 50 + [1] * 50)

    # Corrupt 3 labels intentionally
    corrupted_indices = [5, 45, 80]
    y_corrupted = y_true.copy()
    for idx in corrupted_indices:
        y_corrupted[idx] = 1 - y_true[idx]

    df = pd.DataFrame(X_data, columns=["feat1", "feat2"])
    df["target"] = y_corrupted

    pipeline = PreprocessPipeline(target_col="target", random_state=42)
    X_trans, y_enc, _ = pipeline.fit_transform(df, target_col="target")

    results = detect_label_errors(
        df=df,
        target_col="target",
        target_type="classification",
        preprocessed_X=X_trans,
        encoded_y=y_enc,
        target_encoder=pipeline.target_encoder_,
        random_state=42,
    )

    flagged_indices = [item["row_index"] for item in results["review_queue"]]
    # At least 2 of the 3 corrupted samples must be captured in the review queue
    intersection = set(corrupted_indices).intersection(set(flagged_indices))
    assert len(intersection) >= 2, f"Expected corrupted indices flagged, got {flagged_indices}"
    assert results["total_issues_found"] > 0


def test_label_errors_edge_cases():
    # Single class dataset
    df_single = pd.DataFrame({"x": [1, 2, 3, 4], "y": [0, 0, 0, 0]})
    res = detect_label_errors(
        df=df_single,
        target_col="y",
        target_type="classification",
        preprocessed_X=np.array([[1], [2], [3], [4]]),
        encoded_y=np.array([0, 0, 0, 0]),
    )
    assert res["total_issues_found"] == 0
    assert "only 1" in res["summary"]["message"]
