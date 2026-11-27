"""Unit tests for detective.leakage module."""

import numpy as np
import pandas as pd
import pytest

from detective.leakage import detect_leakage
from detective.preprocess import PreprocessPipeline


def test_detect_exact_copy_leakage():
    np.random.seed(42)
    n = 100
    df = pd.DataFrame(
        {
            "feature1": np.random.normal(0, 1, n),
            "feature2": np.random.uniform(10, 50, n),
            "target": np.random.choice([0, 1], size=n),
        }
    )
    # Inject exact copy with slight rename
    df["target_copy"] = df["target"]

    pipeline = PreprocessPipeline(target_col="target", random_state=42)
    X, y, _ = pipeline.fit_transform(df, target_col="target")

    res = detect_leakage(
        df=df,
        target_col="target",
        target_type="classification",
        preprocessed_X=X,
        encoded_y=y,
        feature_names=pipeline.feature_names_,
        random_state=42,
    )

    suspect_names = [s["feature"] for s in res["suspect_features"]]
    assert "target_copy" in suspect_names
    target_copy_record = next(s for s in res["suspect_features"] if s["feature"] == "target_copy")
    assert target_copy_record["confidence"] == "High"
    assert target_copy_record["suspicion_score"] >= 0.95


def test_detect_correlated_leakage():
    np.random.seed(42)
    n = 120
    target = np.random.choice([0, 1], size=n, p=[0.5, 0.5])
    # Add near-perfect predictive feature with tiny noise
    leaky_feature = target.astype(float) + np.random.normal(0, 0.02, n)

    df = pd.DataFrame(
        {
            "noise_1": np.random.normal(0, 1, n),
            "noise_2": np.random.normal(0, 1, n),
            "outcome_score": leaky_feature,
            "target": target,
        }
    )

    pipeline = PreprocessPipeline(target_col="target", random_state=42)
    X, y, _ = pipeline.fit_transform(df, target_col="target")

    res = detect_leakage(
        df=df,
        target_col="target",
        target_type="classification",
        preprocessed_X=X,
        encoded_y=y,
        feature_names=pipeline.feature_names_,
        random_state=42,
    )

    suspect_names = [s["feature"] for s in res["suspect_features"]]
    assert "outcome_score" in suspect_names
    record = next(s for s in res["suspect_features"] if s["feature"] == "outcome_score")
    assert record["confidence"] in ["High", "Medium"]
    assert record["suspicion_score"] > 0.70
