"""Unit tests for edge cases: missing values, all-numeric, all-categorical, tiny n."""

import numpy as np
import pandas as pd
import pytest

from detective.engine import run_all


def test_heavy_missing_values():
    df = pd.DataFrame(
        {
            "num_mostly_missing": [np.nan] * 35 + [1.0, 2.0, 3.0, 4.0, 5.0],
            "cat_mostly_missing": [np.nan] * 30 + ["A", "B"] * 5,
            "target": [0, 1] * 20,
        }
    )
    report = run_all(df, target_col="target")
    assert report["data_profile"]["overall_missing_pct"] > 50
    assert "preprocess" in report["runtimes_sec"]


def test_all_numeric_dataset():
    df = pd.DataFrame(np.random.normal(size=(40, 5)), columns=[f"col_{i}" for i in range(5)])
    df["target"] = (df["col_0"] > 0).astype(int)
    report = run_all(df, target_col="target")
    assert report["summary"]["overall_severity"] in ["Clean", "Low", "Medium", "High"]


def test_all_categorical_dataset():
    df = pd.DataFrame(
        {
            "c1": ["cat", "dog", "bird"] * 15,
            "c2": ["red", "blue", "green"] * 15,
            "c3": ["yes", "no"] * 22 + ["yes"],
            "target": ["approved", "denied"] * 22 + ["approved"],
        }
    )
    report = run_all(df, target_col="target")
    assert report["data_profile"]["target_type"] == "classification"
    assert report["summary"]["data_health_score"] > 0


def test_tiny_dataset():
    df = pd.DataFrame(
        {
            "a": [1, 2, 3],
            "b": [4, 5, 6],
            "target": [0, 1, 0],
        }
    )
    # Should not crash on tiny n
    report = run_all(df, target_col="target")
    assert report["metadata"]["dataset_rows"] == 3
