"""Unit tests for detective.duplicates module."""

import pandas as pd
import pytest

from detective.duplicates import find_duplicates


def test_exact_duplicates():
    df = pd.DataFrame(
        {
            "a": [1, 2, 3, 1, 2, 5],
            "b": [10, 20, 30, 10, 20, 50],
            "target": [0, 1, 0, 0, 1, 1],
        }
    )
    results = find_duplicates(df, target_col="target")

    assert results["exact_duplicates"]["count"] == 4  # rows 0, 1, 3, 4
    assert set(results["exact_duplicates"]["row_indices"]) == {0, 1, 3, 4}
    assert results["conflicting_duplicates"]["count"] == 0


def test_conflicting_label_duplicates():
    # Rows 0 and 2 have identical features a=1, b=10, but target=0 vs target=1
    df = pd.DataFrame(
        {
            "a": [1, 2, 1, 4],
            "b": [10, 20, 10, 40],
            "target": [0, 1, 1, 0],
        }
    )
    results = find_duplicates(df, target_col="target")

    assert results["conflicting_duplicates"]["count"] == 2
    assert set(results["conflicting_duplicates"]["row_indices"]) == {0, 2}
    assert results["summary"]["severity"] == "High"
    assert results["summary"]["has_conflicting_labels"] is True


def test_key_duplicates_and_train_test_overlap():
    train_df = pd.DataFrame(
        {
            "id": [101, 102, 103, 101],
            "x": [1.0, 2.0, 3.0, 1.0],
            "y": [0, 1, 0, 0],
        }
    )
    test_df = pd.DataFrame(
        {
            "id": [103, 105],
            "x": [3.0, 5.0],
            "y": [0, 1],
        }
    )
    results = find_duplicates(train_df, target_col="y", id_col="id", test_df=test_df)

    assert results["key_duplicates"]["count"] == 2
    assert set(results["key_duplicates"]["row_indices"]) == {0, 3}
    assert results["train_test_overlap"]["count"] == 1
    assert 2 in results["train_test_overlap"]["overlap_rows_train"]
