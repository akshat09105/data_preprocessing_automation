"""
Downloads and builds sample datasets for Data Detective:
1. Breast Cancer (Clean numeric binary classification)
2. Wine (Clean multiclass classification)
3. Titanic (Mixed numerical & categorical tabular classification)
4. Demo Dataset Corrupted (Pre-corrupted with duplicates, leakage, label errors, anomalies)
"""

import os
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.datasets import fetch_openml, load_breast_cancer, load_wine

DATA_DIR = Path(__file__).resolve().parent


def build_samples():
    """Generates and persists the sample datasets."""
    os.makedirs(DATA_DIR, exist_ok=True)
    print("Generating sample datasets...")

    # 1. Breast Cancer
    cancer = load_breast_cancer(as_frame=True)
    cancer_df = cancer.frame.copy()
    cancer_df.rename(columns={"target": "diagnosis"}, inplace=True)
    cancer_path = DATA_DIR / "breast_cancer.csv"
    cancer_df.to_csv(cancer_path, index=False)
    print(f"Saved Breast Cancer ({cancer_df.shape}) to {cancer_path}")

    # 2. Wine
    wine = load_wine(as_frame=True)
    wine_df = wine.frame.copy()
    wine_df.rename(columns={"target": "wine_class"}, inplace=True)
    wine_path = DATA_DIR / "wine.csv"
    wine_df.to_csv(wine_path, index=False)
    print(f"Saved Wine ({wine_df.shape}) to {wine_path}")

    # 3. Titanic (Demographics & Survival)
    # Synthetic realistic Titanic-like dataset if offline, or fetch
    try:
        titanic_raw = fetch_openml("titanic", version=1, as_frame=True, parser="auto")
        titanic_df = titanic_raw.frame[
            ["pclass", "sex", "age", "sibsp", "parch", "fare", "embarked", "survived"]
        ].copy()
        titanic_df["survived"] = titanic_df["survived"].astype(int)
    except Exception:
        # High fidelity synthetic fallback
        rng = np.random.RandomState(42)
        n = 300
        pclass = rng.choice([1, 2, 3], size=n, p=[0.25, 0.25, 0.5])
        sex = rng.choice(["male", "female"], size=n, p=[0.6, 0.4])
        age = rng.normal(30, 14, size=n).clip(1, 80).round(1)
        sibsp = rng.poisson(0.5, size=n)
        parch = rng.poisson(0.4, size=n)
        fare = (pclass * 15.0 + rng.exponential(25.0, size=n)).round(2)
        embarked = rng.choice(["S", "C", "Q"], size=n, p=[0.7, 0.2, 0.1])
        # Logistic survival probability
        logit = (
            -0.8 * pclass
            + 1.8 * (sex == "female").astype(float)
            - 0.02 * age
            + 0.01 * fare
        )
        prob = 1.0 / (1.0 + np.exp(-logit))
        survived = (rng.uniform(size=n) < prob).astype(int)

        titanic_df = pd.DataFrame(
            {
                "passenger_id": [f"TC_{1000+i}" for i in range(n)],
                "pclass": pclass,
                "sex": sex,
                "age": age,
                "sibsp": sibsp,
                "parch": parch,
                "fare": fare,
                "embarked": embarked,
                "survived": survived,
            }
        )

    titanic_path = DATA_DIR / "titanic.csv"
    titanic_df.to_csv(titanic_path, index=False)
    print(f"Saved Titanic ({titanic_df.shape}) to {titanic_path}")

    # 4. Pre-corrupted Demo Dataset (Built on Titanic or Cancer for instant app testing)
    demo_df = titanic_df.copy().head(250)
    # Ensure passenger_id is present
    if "passenger_id" not in demo_df.columns:
        demo_df.insert(0, "passenger_id", [f"PAS_{100+i}" for i in range(len(demo_df))])

    rng = np.random.RandomState(42)

    # A. Inject Target Leakage Column FIRST so duplicates copy it identically
    noise = rng.normal(0, 0.02, size=len(demo_df))
    demo_df["final_outcome_score"] = demo_df["survived"].astype(float) + noise

    # B. Inject Label Errors (flip labels on 8 obvious rows)
    flip_indices = [30, 45, 60, 75, 90, 105, 120, 135]
    for idx in flip_indices:
        demo_df.loc[idx, "survived"] = 1 - demo_df.loc[idx, "survived"]

    # C. Inject Extreme Anomalies (perturbed fare and age at 8+ std deviations)
    demo_df.loc[18, "fare"] = 9850.0  # Normal fare is 10-200
    demo_df.loc[42, "age"] = 195.0    # Normal age is 0-80

    # D. Inject Exact Duplicates (5 rows completely identical)
    dup_rows = demo_df.iloc[[10, 11, 12, 13, 14]].copy()
    demo_df = pd.concat([demo_df, dup_rows], ignore_index=True)

    # E. Inject Conflicting Label Duplicate (Identical features, opposite survival label)
    conflict_row = demo_df.iloc[[25]].copy()
    conflict_row["survived"] = 1 - conflict_row["survived"].values[0]
    demo_df = pd.concat([demo_df, conflict_row], ignore_index=True)

    demo_path = DATA_DIR / "demo_dataset_corrupted.csv"
    demo_df.to_csv(demo_path, index=False)
    print(f"Saved Pre-corrupted Demo Dataset ({demo_df.shape}) to {demo_path}")
    print("All sample datasets successfully generated!")


if __name__ == "__main__":
    build_samples()
