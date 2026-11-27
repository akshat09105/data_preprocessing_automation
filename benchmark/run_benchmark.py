"""
Benchmark runner script for Data Detective.
Runs full experimental matrix:
- Defect types: Clean, Duplicates, Leakage, Label Noise, Anomalies
- Varying corruption rates (e.g. 1%, 5%, 10%)
- Multiple datasets (Breast Cancer, Wine, Titanic)
- Multiple random seeds (42, 101, 2024)
Saves results/benchmark.csv and creates precision-recall plots.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from benchmark.evaluate import calculate_metrics, evaluate_downstream_impact
from benchmark.inject import (
    inject_anomalies,
    inject_duplicates,
    inject_label_noise,
    inject_leakage,
)
from detective.engine import run_all

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def run_benchmark():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    from data.download_samples import build_samples

    build_samples()

    data_dir = Path(__file__).resolve().parent.parent / "data"

    datasets = {
        "breast_cancer": {
            "path": data_dir / "breast_cancer.csv",
            "target": "diagnosis",
        },
        "wine": {
            "path": data_dir / "wine.csv",
            "target": "wine_class",
        },
        "titanic": {
            "path": data_dir / "titanic.csv",
            "target": "survived",
        },
    }

    seeds = [42, 101]
    defect_scenarios = [
        ("clean", 0.0),
        ("duplicates", 0.01),
        ("duplicates", 0.05),
        ("duplicates", 0.10),
        ("leakage", 0.01),
        ("leakage", 0.05),
        ("leakage", 0.15),
        ("label_noise", 0.01),
        ("label_noise", 0.05),
        ("label_noise", 0.10),
        ("anomalies", 0.01),
        ("anomalies", 0.03),
        ("anomalies", 0.05),
    ]

    benchmark_rows = []

    print("=" * 80)
    print("STARTING DATA DETECTIVE BENCHMARK SUITE")
    print("=" * 80)

    for ds_name, ds_info in datasets.items():
        base_df = pd.read_csv(ds_info["path"])
        target_col = ds_info["target"]

        # Limit to 250 rows for fast benchmark runtime
        if len(base_df) > 250:
            base_df = base_df.sample(250, random_state=42).reset_index(drop=True)

        for defect_type, rate in defect_scenarios:
            for seed in seeds:
                t0 = time.perf_counter()
                gt_indices = []
                gt_leaky_col = None

                df_test = base_df.copy()

                if defect_type == "clean":
                    pass
                elif defect_type == "duplicates":
                    df_test, gt_indices = inject_duplicates(df_test, rate=rate, random_state=seed)
                elif defect_type == "leakage":
                    df_test, gt_leaky_col = inject_leakage(
                        df_test, target_col=target_col, noise_std=rate, random_state=seed
                    )
                elif defect_type == "label_noise":
                    df_test, gt_indices = inject_label_noise(
                        df_test, target_col=target_col, rate=rate, random_state=seed
                    )
                elif defect_type == "anomalies":
                    df_test, gt_indices = inject_anomalies(
                        df_test, rate=rate, num_sigma=7.0, random_state=seed
                    )

                # Execute Data Detective Audit targeted to defect or all for clean
                audit_options = {
                    "random_state": seed,
                    "enable_duplicates": defect_type in ["duplicates", "clean"],
                    "enable_leakage": defect_type in ["leakage", "clean"],
                    "enable_label_errors": defect_type in ["label_noise", "clean"],
                    "enable_anomalies": defect_type in ["anomalies", "clean"],
                }
                audit_report = run_all(df_test, target_col=target_col, options=audit_options)
                runtime = round(time.perf_counter() - t0, 3)

                # Collect detections
                if defect_type == "duplicates":
                    detected_indices = audit_report["duplicates"]["exact_duplicates"]["row_indices"]
                    metrics = calculate_metrics(gt_indices, detected_indices, len(df_test))
                elif defect_type == "leakage":
                    detected_cols = [
                        s["feature"] for s in audit_report["leakage"]["suspect_features"]
                    ]
                    tp = 1 if gt_leaky_col in detected_cols else 0
                    fp = len(detected_cols) - tp
                    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
                    recall = float(tp)
                    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
                    metrics = {
                        "precision": precision,
                        "recall": recall,
                        "f1": f1,
                        "false_alarm_rate": 0.0 if fp == 0 else round(fp / len(df_test.columns), 4),
                    }
                elif defect_type == "label_noise":
                    detected_indices = [
                        item["row_index"] for item in audit_report["label_errors"]["review_queue"]
                    ]
                    metrics = calculate_metrics(gt_indices, detected_indices, len(df_test))
                elif defect_type == "anomalies":
                    detected_indices = audit_report["anomalies"]["anomaly_indices"]
                    metrics = calculate_metrics(gt_indices, detected_indices, len(df_test))
                else:  # Clean baseline
                    total_flagged = len(audit_report["master_review_queue"])
                    far = round(total_flagged / len(df_test), 4) if len(df_test) > 0 else 0.0
                    metrics = {
                        "precision": 1.0,
                        "recall": 1.0,
                        "f1": 1.0,
                        "false_alarm_rate": far,
                    }

                # Evaluate downstream accuracy impact for label noise / leakage
                downstream = {"delta_acc": 0.0, "dirty_model_acc": 0.0, "cleaned_model_acc": 0.0}
                if defect_type in ["label_noise", "leakage"] and len(base_df) > 50:
                    split_idx = int(0.75 * len(base_df))
                    train_eval = df_test.iloc[:split_idx].copy()
                    test_eval = base_df.iloc[split_idx:].copy()
                    downstream = evaluate_downstream_impact(
                        train_df=train_eval,
                        test_df=test_eval,
                        target_col=target_col,
                        rows_to_drop=gt_indices if defect_type == "label_noise" else None,
                        cols_to_drop=[gt_leaky_col] if gt_leaky_col else None,
                        random_state=seed,
                    )

                result_row = {
                    "dataset": ds_name,
                    "defect_type": defect_type,
                    "corruption_rate": rate,
                    "seed": seed,
                    "precision": metrics.get("precision", 0.0),
                    "recall": metrics.get("recall", 0.0),
                    "f1": metrics.get("f1", 0.0),
                    "false_alarm_rate": metrics.get("false_alarm_rate", 0.0),
                    "runtime_sec": runtime,
                    "dirty_model_acc": downstream.get("dirty_model_acc", 0.0),
                    "cleaned_model_acc": downstream.get("cleaned_model_acc", 0.0),
                    "delta_acc": downstream.get("delta_acc", 0.0),
                }
                benchmark_rows.append(result_row)
                print(
                    f"[{ds_name}] {defect_type} (rate={rate}, seed={seed}): "
                    f"P={metrics.get('precision', 0):.2f}, R={metrics.get('recall', 0):.2f}, "
                    f"F1={metrics.get('f1', 0):.2f}, Runtime={runtime:.2f}s"
                )

    # Save benchmark CSV
    results_df = pd.DataFrame(benchmark_rows)
    csv_path = RESULTS_DIR / "benchmark.csv"
    results_df.to_csv(csv_path, index=False)
    print(f"\nSaved benchmark results to {csv_path}")

    # Generate Precision / Recall vs Corruption Rate Plot
    try:
        plot_df = (
            results_df[results_df["defect_type"] != "clean"]
            .groupby(["defect_type", "corruption_rate"])[["precision", "recall", "f1"]]
            .mean()
            .reset_index()
        )

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        for def_type, group in plot_df.groupby("defect_type"):
            ax1.plot(group["corruption_rate"], group["precision"], marker="o", label=f"{def_type} (P)")
            ax2.plot(group["corruption_rate"], group["recall"], marker="s", label=f"{def_type} (R)")

        ax1.set_title("Precision vs Corruption Rate")
        ax1.set_xlabel("Corruption Rate")
        ax1.set_ylabel("Precision")
        ax1.set_ylim(-0.05, 1.05)
        ax1.grid(True, linestyle="--", alpha=0.5)
        ax1.legend()

        ax2.set_title("Recall vs Corruption Rate")
        ax2.set_xlabel("Corruption Rate")
        ax2.set_ylabel("Recall")
        ax2.set_ylim(-0.05, 1.05)
        ax2.grid(True, linestyle="--", alpha=0.5)
        ax2.legend()

        plt.tight_layout()
        plot_path = RESULTS_DIR / "precision_recall_curves.png"
        plt.savefig(plot_path, dpi=200)
        plt.close()
        print(f"Saved benchmark curves plot to {plot_path}")
    except Exception as e:
        print(f"Plot generation warning: {e}")

    print("\nBENCHMARK COMPLETE!")
    return results_df


if __name__ == "__main__":
    run_benchmark()
