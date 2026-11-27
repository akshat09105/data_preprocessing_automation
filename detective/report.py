"""
Report module for Data Detective.
Generates human-readable action summaries and exports findings in multiple formats:
CSV (flagged rows), JSON (full payload), and formatted multi-sheet Excel workbooks.
"""

import io
import json
import logging
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger("data_detective.report")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s [%(name)s]: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def generate_recommendations(report: Dict[str, Any]) -> List[str]:
    """Derives actionable, human-oriented recommendations from audit findings."""
    recs = []
    summary = report.get("summary", {})

    # 1. Conflicting labels
    if summary.get("conflicting_labels", 0) > 0:
        recs.append(
            f"CRITICAL: Found {summary['conflicting_labels']} rows with identical feature vectors "
            "but conflicting target values. Inspect these rows in the Duplicates tab; they indicate "
            "labeling ambiguity or missing distinguishing features."
        )

    # 2. Target leakage
    if summary.get("leakage_suspects", 0) > 0:
        suspects = [
            f"{s['feature']} ({s['confidence']} confidence)"
            for s in report.get("leakage", {}).get("suspect_features", [])
        ]
        recs.append(
            f"HIGH PRIORITY: {summary['leakage_suspects']} feature(s) exhibit strong target leakage signals: "
            f"{', '.join(suspects)}. Exclude or sanitize them before training production ML models."
        )

    # 3. Label errors
    if summary.get("label_issue_candidates", 0) > 0:
        recs.append(
            f"RECOMMENDED: Review {summary['label_issue_candidates']} candidate label issues flagged by "
            "Cleanlab and out-of-fold cross-validation. Validate ground truth before model deployment."
        )

    # 4. Duplicates
    if summary.get("total_duplicates", 0) > 0:
        recs.append(
            f"ADVISORY: Detected {summary['total_duplicates']} exact duplicate rows. "
            "Consider deduplicating to prevent test-leakage and inflated performance metrics."
        )

    # 5. Anomalies
    if summary.get("anomalies_flagged", 0) > 0:
        recs.append(
            f"NOTICE: Highlighted {summary['anomalies_flagged']} multidimensional anomalies. "
            "Review their feature attribution scores to confirm whether they represent valid rare "
            "events or measurement corruption."
        )

    if not recs:
        recs.append(
            "DATASET CLEAN: No prominent defects detected. The dataset appears well-conditioned for classical ML modeling."
        )

    return recs


def export_to_json(report: Dict[str, Any]) -> str:
    """Exports full audit report as pretty-printed JSON string."""
    return json.dumps(report, indent=2, default=str)


def export_master_queue_csv(report: Dict[str, Any], df: Optional[pd.DataFrame] = None) -> str:
    """Exports the Master Review Queue as a CSV string, joined with original data if provided."""
    queue = report.get("master_review_queue", [])
    if not queue:
        return "row_index,priority_score,overall_severity,flag_count,reasons\n"

    queue_df = pd.DataFrame(
        [
            {
                "row_index": item["row_index"],
                "priority_score": item["priority_score"],
                "overall_severity": item["overall_severity"],
                "flag_count": item["flag_count"],
                "reasons": item["reasons"],
            }
            for item in queue
        ]
    )

    if df is not None and not df.empty:
        # Join with original dataframe rows
        merged = queue_df.merge(
            df.reset_index().rename(columns={"index": "row_index"}),
            on="row_index",
            how="left",
        )
        return merged.to_csv(index=False)
    else:
        return queue_df.to_csv(index=False)


def export_to_excel(report: Dict[str, Any], df: Optional[pd.DataFrame] = None) -> bytes:
    """
    Exports comprehensive audit report into an Excel workbook (.xlsx)
    with dedicated sheets: Summary, Duplicates, Leakage, Label_Review, Anomalies, Data_Profile.
    """
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Sheet 1: Summary & Metrics
        summary = report.get("summary", {})
        meta = report.get("metadata", {})
        recs = generate_recommendations(report)

        summary_rows = [
            {"Metric": "Data Health Score", "Value": f"{summary.get('data_health_score', 0)}/100"},
            {"Metric": "Overall Severity", "Value": summary.get("overall_severity", "Clean")},
            {"Metric": "Total Rows", "Value": meta.get("dataset_rows", 0)},
            {"Metric": "Total Columns", "Value": meta.get("dataset_cols", 0)},
            {"Metric": "Target Column", "Value": meta.get("target_col", "None")},
            {"Metric": "Exact Duplicates", "Value": summary.get("total_duplicates", 0)},
            {"Metric": "Conflicting Label Rows", "Value": summary.get("conflicting_labels", 0)},
            {"Metric": "Leakage Suspects", "Value": summary.get("leakage_suspects", 0)},
            {"Metric": "Label Error Candidates", "Value": summary.get("label_issue_candidates", 0)},
            {"Metric": "Anomalies Flagged", "Value": summary.get("anomalies_flagged", 0)},
            {"Metric": "Master Queue Rows", "Value": len(report.get("master_review_queue", []))},
        ]
        pd.DataFrame(summary_rows).to_excel(writer, sheet_name="Summary", index=False)

        # Recommendations block
        recs_df = pd.DataFrame([{"Action Recommendations": r} for r in recs])
        recs_df.to_excel(writer, sheet_name="Recommendations", index=False)

        # Sheet 2: Duplicates
        dup_details = []
        # Exact
        exact_details = report.get("duplicates", {}).get("exact_duplicates", {}).get("details", [])
        for grp in exact_details:
            for idx in grp["row_indices"]:
                dup_details.append(
                    {
                        "row_index": idx,
                        "duplicate_type": "Exact",
                        "group_id": grp["group_id"],
                        "group_size": grp["count"],
                    }
                )
        # Conflicting
        conflict_details = (
            report.get("duplicates", {}).get("conflicting_duplicates", {}).get("groups", [])
        )
        for grp in conflict_details:
            for idx in grp["row_indices"]:
                dup_details.append(
                    {
                        "row_index": idx,
                        "duplicate_type": "Conflicting Target",
                        "group_id": grp["conflict_group_id"],
                        "group_size": grp["count"],
                    }
                )
        if dup_details:
            pd.DataFrame(dup_details).to_excel(writer, sheet_name="Duplicates", index=False)
        else:
            pd.DataFrame([{"Message": "No duplicates detected."}]).to_excel(
                writer, sheet_name="Duplicates", index=False
            )

        # Sheet 3: Leakage
        leak_suspects = report.get("leakage", {}).get("suspect_features", [])
        if leak_suspects:
            leak_rows = []
            for item in leak_suspects:
                leak_rows.append(
                    {
                        "feature": item["feature"],
                        "suspicion_score": item["suspicion_score"],
                        "confidence": item["confidence"],
                        "single_feature_score": item["single_feature_score"],
                        "permutation_importance": item["permutation_importance"],
                        "score_drop_delta": item["score_drop_delta"],
                        "evidence": "; ".join(item.get("evidence", [])),
                        "recommendation": item.get("recommendation", ""),
                    }
                )
            pd.DataFrame(leak_rows).to_excel(writer, sheet_name="Leakage", index=False)
        else:
            pd.DataFrame([{"Message": "No target leakage detected."}]).to_excel(
                writer, sheet_name="Leakage", index=False
            )

        # Sheet 4: Label Review Queue
        label_queue = report.get("label_errors", {}).get("review_queue", [])
        if label_queue:
            label_df = pd.DataFrame(label_queue)
            label_df.to_excel(writer, sheet_name="Label_Review", index=False)
        else:
            pd.DataFrame([{"Message": "No label issues detected or not a classification task."}]).to_excel(
                writer, sheet_name="Label_Review", index=False
            )

        # Sheet 5: Anomalies
        anom_list = report.get("anomalies", {}).get("ranked_anomalies", [])
        if anom_list:
            anom_rows = []
            for item in anom_list:
                anom_rows.append(
                    {
                        "row_index": item["row_index"],
                        "anomaly_score": item["anomaly_score"],
                        "severity": item["severity"],
                        "iso_forest_score": item.get("iso_forest_score", 0),
                        "pca_score": item.get("pca_score", 0),
                        "lof_score": item.get("lof_score", 0),
                        "primary_reason": item.get("primary_reason", ""),
                    }
                )
            pd.DataFrame(anom_rows).to_excel(writer, sheet_name="Anomalies", index=False)
        else:
            pd.DataFrame([{"Message": "No anomalies flagged."}]).to_excel(
                writer, sheet_name="Anomalies", index=False
            )

        # Sheet 6: Data Profile
        prof = report.get("data_profile", {})
        if prof:
            prof_summary = [
                {"Attribute": "Total Rows", "Value": prof.get("total_rows", 0)},
                {"Attribute": "Total Columns", "Value": prof.get("total_cols", 0)},
                {"Attribute": "Overall Missing %", "Value": f"{prof.get('overall_missing_pct', 0)}%"},
                {"Attribute": "Target Type", "Value": prof.get("target_type", "None")},
                {"Attribute": "Memory (MB)", "Value": prof.get("memory_usage_mb", 0)},
                {"Attribute": "Numeric Features", "Value": ", ".join(prof.get("num_cols", []))},
                {"Attribute": "Categorical Features", "Value": ", ".join(prof.get("cat_cols", []))},
                {"Attribute": "ID Columns", "Value": ", ".join(prof.get("id_cols", []))},
            ]
            pd.DataFrame(prof_summary).to_excel(writer, sheet_name="Data_Profile", index=False)

    return output.getvalue()
