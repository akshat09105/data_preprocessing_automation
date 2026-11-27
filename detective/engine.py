"""
Engine module for Data Detective.
Coordinates all detection modules, records runtime performance, isolates module
failures with error boundaries, and synthesizes the Master Review Queue.
"""

import logging
import time
from typing import Any, Dict, List, Optional

import pandas as pd

from detective.anomalies import detect_anomalies
from detective.duplicates import find_duplicates
from detective.label_errors import detect_label_errors
from detective.leakage import detect_leakage
from detective.preprocess import PreprocessPipeline

logger = logging.getLogger("data_detective.engine")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s [%(name)s]: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def run_all(
    df: pd.DataFrame,
    target_col: Optional[str] = None,
    id_col: Optional[str] = None,
    test_df: Optional[pd.DataFrame] = None,
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Executes end-to-end data audit across duplicates, leakage, label errors, and anomalies.

    Args:
        df: Input tabular DataFrame.
        target_col: Name of the target column.
        id_col: Optional ID or primary key column.
        test_df: Optional evaluation test DataFrame for cross-dataset overlap checks.
        options: Configuration dict (e.g. enable_duplicates, enable_leakage, contamination).

    Returns:
        Unified audit report dictionary with module outputs, runtime breakdown,
        and synthesized master review queue.
    """
    start_total_time = time.perf_counter()
    options = options or {}

    enable_duplicates = options.get("enable_duplicates", True)
    enable_leakage = options.get("enable_leakage", True)
    enable_label_errors = options.get("enable_label_errors", True)
    enable_anomalies = options.get("enable_anomalies", True)
    contamination = options.get("contamination", 0.05)
    random_state = options.get("random_state", 42)

    report: Dict[str, Any] = {
        "metadata": {
            "dataset_rows": len(df),
            "dataset_cols": len(df.columns),
            "target_col": target_col,
            "id_col": id_col,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "runtimes_sec": {},
        "data_profile": {},
        "duplicates": {},
        "leakage": {},
        "label_errors": {},
        "anomalies": {},
        "master_review_queue": [],
        "summary": {
            "data_health_score": 100,
            "total_duplicates": 0,
            "conflicting_labels": 0,
            "leakage_suspects": 0,
            "label_issue_candidates": 0,
            "anomalies_flagged": 0,
            "overall_severity": "Clean",
            "findings_count": 0,
        },
        "module_errors": {},
    }

    if df.empty:
        report["summary"]["overall_severity"] = "Empty Dataset"
        return report

    # 1. Preprocessing Pipeline
    t0 = time.perf_counter()
    pipeline = PreprocessPipeline(
        target_col=target_col, id_col=id_col, random_state=random_state
    )
    try:
        X_trans, y_enc, profile = pipeline.fit_transform(df, target_col=target_col, id_col=id_col)
        report["data_profile"] = profile
        report["runtimes_sec"]["preprocess"] = round(time.perf_counter() - t0, 3)
    except Exception as e:
        logger.error("Preprocessing failed: %s", e, exc_info=True)
        report["module_errors"]["preprocess"] = str(e)
        X_trans, y_enc = None, None

    # 2. Duplicates Audit
    if enable_duplicates:
        t0 = time.perf_counter()
        try:
            dup_results = find_duplicates(
                df=df, target_col=target_col, id_col=id_col, test_df=test_df
            )
            report["duplicates"] = dup_results
        except Exception as e:
            logger.error("Duplicates audit failed: %s", e, exc_info=True)
            report["module_errors"]["duplicates"] = str(e)
            report["duplicates"] = {"summary": {"severity": "Error"}, "error": str(e)}
        report["runtimes_sec"]["duplicates"] = round(time.perf_counter() - t0, 3)

    # 3. Leakage Audit
    if enable_leakage and target_col and target_col in df.columns:
        t0 = time.perf_counter()
        try:
            leak_results = detect_leakage(
                df=df,
                target_col=target_col,
                target_type=pipeline.target_type_,
                preprocessed_X=X_trans,
                encoded_y=y_enc,
                feature_names=pipeline.feature_names_,
                random_state=random_state,
            )
            report["leakage"] = leak_results
        except Exception as e:
            logger.error("Leakage audit failed: %s", e, exc_info=True)
            report["module_errors"]["leakage"] = str(e)
            report["leakage"] = {"summary": {"severity": "Error"}, "error": str(e)}
        report["runtimes_sec"]["leakage"] = round(time.perf_counter() - t0, 3)

    # 4. Label Errors Audit
    if enable_label_errors and target_col and target_col in df.columns:
        t0 = time.perf_counter()
        try:
            if pipeline.target_type_ == "classification" and X_trans is not None and y_enc is not None:
                lbl_results = detect_label_errors(
                    df=df,
                    target_col=target_col,
                    target_type=pipeline.target_type_,
                    preprocessed_X=X_trans,
                    encoded_y=y_enc,
                    target_encoder=pipeline.target_encoder_,
                    random_state=random_state,
                )
                report["label_errors"] = lbl_results
            else:
                report["label_errors"] = {
                    "review_queue": [],
                    "summary": {
                        "severity": "N/A",
                        "message": (
                            "Label audit skipped (requires classification target and valid features)."
                        ),
                    },
                }
        except Exception as e:
            logger.error("Label error audit failed: %s", e, exc_info=True)
            report["module_errors"]["label_errors"] = str(e)
            report["label_errors"] = {"summary": {"severity": "Error"}, "error": str(e)}
        report["runtimes_sec"]["label_errors"] = round(time.perf_counter() - t0, 3)

    # 5. Anomalies Audit
    if enable_anomalies and X_trans is not None and X_trans.shape[1] > 0:
        t0 = time.perf_counter()
        try:
            anom_results = detect_anomalies(
                df=df,
                preprocessed_X=X_trans,
                feature_names=pipeline.feature_names_,
                contamination=contamination,
                random_state=random_state,
            )
            report["anomalies"] = anom_results
        except Exception as e:
            logger.error("Anomaly audit failed: %s", e, exc_info=True)
            report["module_errors"]["anomalies"] = str(e)
            report["anomalies"] = {"summary": {"severity": "Error"}, "error": str(e)}
        report["runtimes_sec"]["anomalies"] = round(time.perf_counter() - t0, 3)

    # 6. Synthesize Master Review Queue
    # Combines rows flagged by multiple detectors
    master_queue_dict: Dict[int, Dict[str, Any]] = {}

    # Conflicting label duplicates
    if report.get("duplicates", {}).get("conflicting_duplicates", {}).get("groups"):
        for grp in report["duplicates"]["conflicting_duplicates"]["groups"]:
            for r_idx in grp["row_indices"]:
                if r_idx not in master_queue_dict:
                    master_queue_dict[r_idx] = {
                        "row_index": r_idx,
                        "flagged_reasons": [],
                        "severities": [],
                        "details": {},
                    }
                master_queue_dict[r_idx]["flagged_reasons"].append("Conflicting Label Duplicate")
                master_queue_dict[r_idx]["severities"].append("High")
                master_queue_dict[r_idx]["details"]["conflicting_group"] = grp["conflict_group_id"]

    # Exact duplicates
    if report.get("duplicates", {}).get("exact_duplicates", {}).get("row_indices"):
        for r_idx in report["duplicates"]["exact_duplicates"]["row_indices"]:
            if r_idx not in master_queue_dict:
                master_queue_dict[r_idx] = {
                    "row_index": r_idx,
                    "flagged_reasons": [],
                    "severities": [],
                    "details": {},
                }
            master_queue_dict[r_idx]["flagged_reasons"].append("Exact Duplicate")
            master_queue_dict[r_idx]["severities"].append("Medium")

    # Label issues
    if report.get("label_errors", {}).get("review_queue"):
        for item in report["label_errors"]["review_queue"]:
            r_idx = item["row_index"]
            if r_idx not in master_queue_dict:
                master_queue_dict[r_idx] = {
                    "row_index": r_idx,
                    "flagged_reasons": [],
                    "severities": [],
                    "details": {},
                }
            master_queue_dict[r_idx]["flagged_reasons"].append("Potential Label Error")
            master_queue_dict[r_idx]["severities"].append(item.get("severity", "Medium"))
            master_queue_dict[r_idx]["details"]["given_label"] = item.get("given_label")
            master_queue_dict[r_idx]["details"]["suggested_label"] = item.get("suggested_label")
            master_queue_dict[r_idx]["details"]["label_confidence"] = item.get("model_confidence")

    # Anomalies
    if report.get("anomalies", {}).get("ranked_anomalies"):
        for anom in report["anomalies"]["ranked_anomalies"]:
            r_idx = anom["row_index"]
            if r_idx not in master_queue_dict:
                master_queue_dict[r_idx] = {
                    "row_index": r_idx,
                    "flagged_reasons": [],
                    "severities": [],
                    "details": {},
                }
            master_queue_dict[r_idx]["flagged_reasons"].append("Statistical Anomaly")
            master_queue_dict[r_idx]["severities"].append(anom.get("severity", "Medium"))
            master_queue_dict[r_idx]["details"]["anomaly_score"] = anom.get("anomaly_score")
            master_queue_dict[r_idx]["details"]["anomaly_reason"] = anom.get("primary_reason")

    # Format Master Review Queue
    master_queue = []
    for r_idx, data in master_queue_dict.items():
        reasons = list(set(data["flagged_reasons"]))
        multi_flagged = len(reasons) > 1
        severities = data["severities"]

        if "High" in severities or multi_flagged:
            overall_sev = "High"
        elif "Medium" in severities:
            overall_sev = "Medium"
        else:
            overall_sev = "Low"

        # Calculate Priority Score (1-100)
        base_priority = 40
        if "High" in severities:
            base_priority += 30
        if multi_flagged:
            base_priority += 25
        if "Conflicting Label Duplicate" in reasons:
            base_priority += 15
        priority_score = min(100, base_priority)

        master_queue.append(
            {
                "row_index": r_idx,
                "priority_score": priority_score,
                "overall_severity": overall_sev,
                "flag_count": len(reasons),
                "reasons": ", ".join(reasons),
                "details": data["details"],
            }
        )

    # Sort descending by priority score and flag count
    master_queue.sort(key=lambda x: (x["priority_score"], x["flag_count"]), reverse=True)
    report["master_review_queue"] = master_queue

    # 7. Aggregate Summary & Health Score
    exact_dups = report.get("duplicates", {}).get("exact_duplicates", {}).get("count", 0)
    conflict_dups = report.get("duplicates", {}).get("conflicting_duplicates", {}).get("count", 0)
    leak_suspects = len(report.get("leakage", {}).get("suspect_features", []))
    label_issues = len(report.get("label_errors", {}).get("review_queue", []))
    anom_count = len(report.get("anomalies", {}).get("ranked_anomalies", []))

    total_findings = exact_dups + conflict_dups + (leak_suspects * 10) + label_issues + anom_count

    # Health score calculation (out of 100)
    n_rows = len(df)
    penalty = 0.0
    if n_rows > 0:
        penalty += (conflict_dups / n_rows) * 120.0
        penalty += (exact_dups / n_rows) * 40.0
        penalty += (label_issues / n_rows) * 80.0
        penalty += (anom_count / n_rows) * 20.0
    if leak_suspects > 0:
        penalty += leak_suspects * 15.0

    health_score = max(0, min(100, int(round(100.0 - penalty))))

    severities_all = [
        report.get("duplicates", {}).get("summary", {}).get("severity", "Clean"),
        report.get("leakage", {}).get("summary", {}).get("severity", "Clean"),
        report.get("label_errors", {}).get("summary", {}).get("severity", "Clean"),
        report.get("anomalies", {}).get("summary", {}).get("severity", "Clean"),
    ]

    if "High" in severities_all:
        overall_severity = "High"
    elif "Medium" in severities_all:
        overall_severity = "Medium"
    elif "Low" in severities_all:
        overall_severity = "Low"
    else:
        overall_severity = "Clean"

    report["summary"].update(
        {
            "data_health_score": health_score,
            "total_duplicates": exact_dups,
            "conflicting_labels": conflict_dups,
            "leakage_suspects": leak_suspects,
            "label_issue_candidates": label_issues,
            "anomalies_flagged": anom_count,
            "overall_severity": overall_severity,
            "findings_count": total_findings,
        }
    )

    total_runtime = round(time.perf_counter() - start_total_time, 3)
    report["runtimes_sec"]["total"] = total_runtime

    logger.info(
        "Engine run complete in %.2fs. Health Score: %d/100, Severity: %s, Master Queue: %d rows",
        total_runtime,
        health_score,
        overall_severity,
        len(master_queue),
    )

    return report
