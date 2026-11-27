"""Unit tests for detective.engine and report modules."""

import json
import numpy as np
import pandas as pd
import pytest

from detective.engine import run_all
from detective.report import (
    export_master_queue_csv,
    export_to_excel,
    export_to_json,
    generate_recommendations,
)


def test_engine_run_all_and_exports():
    np.random.seed(42)
    df = pd.DataFrame(
        {
            "id": [f"ID_{i}" for i in range(50)],
            "age": [25 + (i % 30) for i in range(50)],
            "salary": [40000.0 + i * 800 for i in range(50)],
            "target": [0, 1] * 25,
        }
    )
    # Inject 1 duplicate
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)

    report = run_all(df, target_col="target", id_col="id")

    assert report["summary"]["data_health_score"] >= 0
    assert report["metadata"]["dataset_rows"] == 51
    assert "preprocess" in report["runtimes_sec"]
    assert "duplicates" in report["runtimes_sec"]

    # Verify recommendations
    recs = generate_recommendations(report)
    assert len(recs) > 0

    # Verify JSON export
    json_str = export_to_json(report)
    parsed = json.loads(json_str)
    assert parsed["metadata"]["dataset_rows"] == 51

    # Verify CSV export
    csv_str = export_master_queue_csv(report, df)
    assert "row_index" in csv_str

    # Verify Excel export
    excel_bytes = export_to_excel(report, df)
    assert len(excel_bytes) > 1000
    assert excel_bytes.startswith(b"PK")  # Zip/XLSX header
