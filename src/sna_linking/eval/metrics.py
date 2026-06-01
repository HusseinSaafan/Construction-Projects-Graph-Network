from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def cluster_summary(df: pd.DataFrame) -> dict[str, float]:
    total = float(len(df))
    if total == 0:
        return {"singleton_ratio": 0.0, "mean_cluster_size": 0.0, "cluster_count": 0.0}
    cluster_sizes = df.groupby("Sub_Community_ID")["PROJECT_ID"].count()
    singletons = float((cluster_sizes == 1).sum())
    return {
        "singleton_ratio": singletons / float(len(cluster_sizes)),
        "mean_cluster_size": float(cluster_sizes.mean()),
        "cluster_count": float(len(cluster_sizes)),
    }


def pair_metrics(predictions: pd.DataFrame, labels: pd.DataFrame) -> dict[str, float]:
    labels = labels.copy()
    labels["project_id_a"] = labels["project_id_a"].astype(str)
    labels["project_id_b"] = labels["project_id_b"].astype(str)
    predictions = predictions.copy()
    predictions["PROJECT_ID"] = predictions["PROJECT_ID"].astype(str)

    merged = labels.merge(
        predictions[["PROJECT_ID", "Sub_Community_ID"]].rename(columns={"PROJECT_ID": "project_id_a"}),
        on="project_id_a",
        how="left",
    ).merge(
        predictions[["PROJECT_ID", "Sub_Community_ID"]].rename(columns={"PROJECT_ID": "project_id_b"}),
        on="project_id_b",
        how="left",
        suffixes=("_a", "_b"),
    )
    merged["pred_same"] = merged["Sub_Community_ID_a"] == merged["Sub_Community_ID_b"]
    merged["label_same"] = merged["same_project"].astype(bool)
    tp = int((merged["pred_same"] & merged["label_same"]).sum())
    fp = int((merged["pred_same"] & ~merged["label_same"]).sum())
    fn = int((~merged["pred_same"] & merged["label_same"]).sum())
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"pair_precision": precision, "pair_recall": recall, "pair_f1": f1}


def save_quality_report(
    output_path: Path,
    validation_summary: dict,
    cluster_metrics: dict,
    pair_eval: dict | None = None,
) -> None:
    report = {
        "validation_summary": validation_summary,
        "cluster_metrics": cluster_metrics,
        "pair_metrics": pair_eval or {},
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2))
