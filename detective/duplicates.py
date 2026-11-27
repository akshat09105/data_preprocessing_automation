"""
Duplicates module for Data Detective.
Detects:
1. Exact duplicate rows.
2. Conflicting label duplicates (identical features, different targets).
3. Primary key / ID column repetitions.
4. Train / Test overlap (if evaluation holdout CSV is provided).
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("data_detective.duplicates")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s [%(name)s]: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def find_duplicates(
    df: pd.DataFrame,
    target_col: Optional[str] = None,
    id_col: Optional[str] = None,
    test_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """
    Audits dataframe for all varieties of duplicates.

    Returns:
        Dict containing counts, group IDs, row indices, conflicting label records,
        ID repeats, and cross-dataset overlap.
    """
    results: Dict[str, Any] = {
        "exact_duplicates": {
            "count": 0,
            "row_indices": [],
            "group_ids": {},
            "details": [],
        },
        "conflicting_duplicates": {
            "count": 0,
            "row_indices": [],
            "groups": [],
            "details": [],
        },
        "key_duplicates": {
            "count": 0,
            "row_indices": [],
            "repeated_keys": {},
        },
        "train_test_overlap": {
            "count": 0,
            "overlap_rows_train": [],
            "overlap_rows_test": [],
        },
        "summary": {
            "total_duplicate_rows": 0,
            "has_conflicting_labels": False,
            "severity": "Low",
        },
    }

    if df.empty:
        return results

    total_rows = len(df)
    cols_to_use = list(df.columns)

    # 1. Exact Duplicate Rows across all columns
    exact_mask = df.duplicated(keep=False)
    if exact_mask.any():
        exact_indices = df.index[exact_mask].tolist()
        results["exact_duplicates"]["count"] = len(exact_indices)
        results["exact_duplicates"]["row_indices"] = exact_indices

        # Assign group IDs for identical row clusters
        exact_df = df[exact_mask]
        group_id = 1
        group_map = {}
        for _, group in exact_df.groupby(list(df.columns), dropna=False):
            indices = group.index.tolist()
            for idx in indices:
                group_map[int(idx)] = f"exact_group_{group_id}"
            results["exact_duplicates"]["details"].append(
                {
                    "group_id": f"exact_group_{group_id}",
                    "row_indices": [int(i) for i in indices],
                    "count": len(indices),
                }
            )
            group_id += 1
        results["exact_duplicates"]["group_ids"] = group_map

    # 2. Conflicting Label Duplicates (Same features, different target)
    if target_col and target_col in df.columns:
        feature_cols = [c for c in cols_to_use if c != target_col]
        if feature_cols:
            # Check duplicates on feature columns alone
            feature_dup_mask = df.duplicated(subset=feature_cols, keep=False)
            if feature_dup_mask.any():
                candidates = df[feature_dup_mask]
                conflicting_groups = []
                conflicting_indices_set = set()
                conflict_group_id = 1

                for _, group in candidates.groupby(feature_cols, dropna=False):
                    unique_targets = group[target_col].dropna().unique()
                    # Check if there is true disagreement (multiple distinct labels or non-null vs null)
                    has_conflict = len(unique_targets) > 1 or (
                        len(unique_targets) == 1 and group[target_col].isna().any()
                    )

                    if has_conflict:
                        grp_indices = [int(i) for i in group.index.tolist()]
                        conflicting_indices_set.update(grp_indices)
                        target_dist = group[target_col].value_counts(dropna=False).to_dict()
                        formatted_dist = {str(k): int(v) for k, v in target_dist.items()}

                        conflicting_groups.append(
                            {
                                "conflict_group_id": f"conflict_group_{conflict_group_id}",
                                "row_indices": grp_indices,
                                "count": len(grp_indices),
                                "target_distribution": formatted_dist,
                            }
                        )
                        conflict_group_id += 1

                conflicting_indices = sorted(list(conflicting_indices_set))
                results["conflicting_duplicates"]["count"] = len(conflicting_indices)
                results["conflicting_duplicates"]["row_indices"] = conflicting_indices
                results["conflicting_duplicates"]["groups"] = conflicting_groups
                results["conflicting_duplicates"]["details"] = conflicting_groups

    # 3. Key-based repeats (ID column)
    if id_col and id_col in df.columns:
        key_mask = df.duplicated(subset=[id_col], keep=False)
        if key_mask.any():
            key_indices = [int(i) for i in df.index[key_mask].tolist()]
            repeated_keys = (
                df.loc[key_mask, id_col]
                .value_counts(dropna=False)
                .head(50)
                .to_dict()
            )
            formatted_keys = {str(k): int(v) for k, v in repeated_keys.items()}
            results["key_duplicates"]["count"] = len(key_indices)
            results["key_duplicates"]["row_indices"] = key_indices
            results["key_duplicates"]["repeated_keys"] = formatted_keys

    # 4. Train / Test overlap (if test_df provided)
    if test_df is not None and not test_df.empty:
        common_cols = [c for c in df.columns if c in test_df.columns]
        if common_cols:
            train_sub = df[common_cols].copy()
            test_sub = test_df[common_cols].copy()
            # Find merged inner matches
            merged = pd.merge(
                train_sub.reset_index(),
                test_sub.reset_index(),
                on=common_cols,
                how="inner",
                suffixes=("_train", "_test"),
            )
            if not merged.empty:
                train_overlap = sorted(list(set(merged["index_train"].astype(int))))
                test_overlap = sorted(list(set(merged["index_test"].astype(int))))
                results["train_test_overlap"]["count"] = len(train_overlap)
                results["train_test_overlap"]["overlap_rows_train"] = train_overlap
                results["train_test_overlap"]["overlap_rows_test"] = test_overlap

    # Summary and Severity
    conflicts_count = results["conflicting_duplicates"]["count"]
    exact_count = results["exact_duplicates"]["count"]
    total_flagged = len(
        set(results["exact_duplicates"]["row_indices"] + results["conflicting_duplicates"]["row_indices"])
    )

    results["summary"]["total_duplicate_rows"] = total_flagged
    results["summary"]["has_conflicting_labels"] = conflicts_count > 0

    if conflicts_count > 0:
        results["summary"]["severity"] = "High"
    elif exact_count > 0.05 * total_rows:
        results["summary"]["severity"] = "Medium"
    elif exact_count > 0:
        results["summary"]["severity"] = "Low"
    else:
        results["summary"]["severity"] = "Clean"

    logger.info(
        "Duplicates audit complete: %d exact duplicates, %d conflicting label rows, Severity: %s",
        exact_count,
        conflicts_count,
        results["summary"]["severity"],
    )

    return results
