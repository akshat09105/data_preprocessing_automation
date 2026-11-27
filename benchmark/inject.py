"""
Defect injection module for Data Detective benchmarking.
Injects known, ground-truth-labeled data defects:
1. Duplicates (1%, 5%, 10% row copies).
2. Target Leakage (synthetic columns derived from target at varying noise levels).
3. Label Noise (1%, 5%, 10% random label flips).
4. Anomalies (1%, 2%, 5% numeric values perturbed by 5-10 standard deviations).
"""

import copy
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


def inject_duplicates(
    df: pd.DataFrame, rate: float = 0.05, random_state: int = 42
) -> Tuple[pd.DataFrame, List[int]]:
    """
    Duplicates a fraction of rows and appends them.
    Returns:
        corrupted_df: DataFrame with duplicates appended.
        injected_indices: Row indices of the duplicated rows in the corrupted DataFrame.
    """
    rng = np.random.RandomState(random_state)
    n = len(df)
    n_dups = max(1, int(round(rate * n)))

    dup_source_indices = rng.choice(df.index, size=n_dups, replace=False)
    dup_rows = df.loc[dup_source_indices].copy()

    # Append duplicate rows
    corrupted_df = pd.concat([df, dup_rows], ignore_index=True)
    injected_indices = list(range(n, n + n_dups))

    return corrupted_df, injected_indices


def inject_leakage(
    df: pd.DataFrame,
    target_col: str,
    noise_std: float = 0.02,
    col_name: str = "leaky_outcome_metric",
    random_state: int = 42,
) -> Tuple[pd.DataFrame, str]:
    """
    Synthesizes a leaky feature column closely coupled to the target.
    Returns:
        corrupted_df: DataFrame with the injected leaky column.
        col_name: Name of the injected leaky column.
    """
    rng = np.random.RandomState(random_state)
    corrupted_df = df.copy()
    target_series = corrupted_df[target_col]

    if pd.api.types.is_numeric_dtype(target_series):
        std_target = target_series.std()
        noise = rng.normal(0, max(0.01, std_target * noise_std), size=len(df))
        corrupted_df[col_name] = target_series.values + noise
    else:
        # Categorical / string target
        unique_cats = target_series.unique()
        cat_map = {c: i for i, c in enumerate(unique_cats)}
        numeric_target = target_series.map(cat_map).values
        noise = rng.normal(0, max(0.01, noise_std), size=len(df))
        corrupted_df[col_name] = numeric_target + noise

    return corrupted_df, col_name


def inject_label_noise(
    df: pd.DataFrame,
    target_col: str,
    rate: float = 0.05,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, List[int]]:
    """
    Randomly flips target labels on classification tasks.
    Returns:
        corrupted_df: DataFrame with flipped labels.
        flipped_indices: List of original row indices whose labels were flipped.
    """
    rng = np.random.RandomState(random_state)
    corrupted_df = df.copy()
    n = len(df)
    n_flips = max(1, int(round(rate * n)))

    flipped_indices = list(rng.choice(df.index, size=n_flips, replace=False))
    unique_classes = list(corrupted_df[target_col].unique())

    if len(unique_classes) < 2:
        return corrupted_df, []

    for idx in flipped_indices:
        current_val = corrupted_df.loc[idx, target_col]
        # Choose a different class
        alt_classes = [c for c in unique_classes if c != current_val]
        corrupted_df.loc[idx, target_col] = rng.choice(alt_classes)

    return corrupted_df, flipped_indices


def inject_anomalies(
    df: pd.DataFrame,
    rate: float = 0.03,
    num_sigma: float = 7.0,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, List[int]]:
    """
    Perturbs numeric feature values by 5-10 standard deviations to create true anomalies.
    Returns:
        corrupted_df: DataFrame with perturbed numeric values.
        anomaly_indices: List of row indices where anomalies were injected.
    """
    rng = np.random.RandomState(random_state)
    corrupted_df = df.copy()
    numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns]

    if not numeric_cols:
        return corrupted_df, []

    n = len(df)
    n_anoms = max(1, int(round(rate * n)))
    anomaly_indices = list(rng.choice(df.index, size=n_anoms, replace=False))

    for idx in anomaly_indices:
        target_feat = rng.choice(numeric_cols)
        # Ensure target column is float to avoid lossy setitem in pandas 3+
        if not pd.api.types.is_float_dtype(corrupted_df[target_feat]):
            corrupted_df[target_feat] = corrupted_df[target_feat].astype(float)

        col_std = corrupted_df[target_feat].std()
        if pd.isna(col_std) or col_std == 0:
            col_std = 1.0

        direction = rng.choice([-1, 1])
        perturbation = direction * num_sigma * col_std
        corrupted_df.loc[idx, target_feat] = float(corrupted_df.loc[idx, target_feat] + perturbation)

    return corrupted_df, anomaly_indices
