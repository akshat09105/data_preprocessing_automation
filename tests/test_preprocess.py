"""Unit tests for detective.preprocess module."""

import numpy as np
import pandas as pd
import pytest

from detective.preprocess import PreprocessPipeline


def test_column_type_detection():
    df = pd.DataFrame(
        {
            "id": [f"user_{i}" for i in range(100)],
            "age": [20 + (i % 50) for i in range(100)],
            "salary": [30000.0 + i * 500 for i in range(100)],
            "category": ["A", "B", "C", "D"] * 25,
            "target": [0, 1] * 50,
        }
    )
    pipeline = PreprocessPipeline()
    col_types = pipeline.detect_column_types(df, target_col="target")

    assert "id" in col_types["id_cols"]
    assert "age" in col_types["num_cols"]
    assert "salary" in col_types["num_cols"]
    assert "category" in col_types["cat_cols"]


def test_target_type_detection():
    pipeline = PreprocessPipeline()

    # Binary classification
    y_bin = pd.Series([0, 1, 0, 1, 1, 0] * 10)
    assert pipeline.detect_target_type(y_bin) == "classification"

    # Multiclass categorical
    y_cat = pd.Series(["dog", "cat", "bird", "dog"] * 10)
    assert pipeline.detect_target_type(y_cat) == "classification"

    # Continuous regression
    y_reg = pd.Series(np.random.normal(50.0, 15.0, 100))
    assert pipeline.detect_target_type(y_reg) == "regression"


def test_preprocess_pipeline_fit_transform():
    df = pd.DataFrame(
        {
            "user_id": [f"ID_{i}" for i in range(60)],
            "feature_num": [1.5 * i for i in range(60)],
            "feature_cat": (["small", "medium", "large"] * 20),
            "target": ([0, 1] * 30),
        }
    )
    # Add some missing values
    df.loc[5, "feature_num"] = np.nan
    df.loc[10, "feature_cat"] = np.nan

    pipeline = PreprocessPipeline(target_col="target")
    X, y, profile = pipeline.fit_transform(df, target_col="target")

    assert X.shape[0] == 60
    assert X.shape[1] > 0
    assert not np.isnan(X).any()  # Imputation verified
    assert y is not None
    assert len(y) == 60
    assert profile["total_rows"] == 60
    assert profile["total_cols"] == 4
    assert profile["overall_missing_pct"] > 0
