from __future__ import annotations

from pathlib import Path

import pandas as pd

from sna_linking.config import load_databricks_config, load_paths
from sna_linking.eval.metrics import cluster_summary, pair_metrics, save_quality_report
from sna_linking.extract.databricks_extract import (
    build_sample_dataframe,
    extract_from_databricks,
    save_raw_snapshot,
)
from sna_linking.graph.location_communities import assign_communities
from sna_linking.graph.subcommunities import assign_subcommunities, load_matching_config
from sna_linking.validation.quality import clean_dataframe, profile_quality


def run_extract(root: Path, use_sample_data: bool = False) -> Path:
    paths = load_paths(root)
    if use_sample_data:
        raw_df = build_sample_dataframe()
    else:
        config = load_databricks_config()
        raw_df = extract_from_databricks(config)
    save_raw_snapshot(raw_df, paths.raw_path)
    return paths.raw_path


def run_validate(root: Path) -> tuple[Path, dict]:
    paths = load_paths(root)
    df = pd.read_parquet(paths.raw_path)
    clean_df = clean_dataframe(df)
    clean_df.to_parquet(paths.validated_path, index=False)
    quality = profile_quality(df)
    return paths.validated_path, quality.to_dict()


def run_communities(root: Path, radius_meters: float = 50.0) -> Path:
    paths = load_paths(root)
    df = pd.read_parquet(paths.validated_path)
    out = assign_communities(df, radius_meters=radius_meters)
    out.to_parquet(paths.community_path, index=False)
    return paths.community_path


def run_subcommunities(root: Path, matching_config_path: Path | None = None) -> Path:
    paths = load_paths(root)
    df = pd.read_parquet(paths.community_path)
    config = load_matching_config(matching_config_path)
    out = assign_subcommunities(df, config=config)
    out.to_parquet(paths.linked_path, index=False)
    return paths.linked_path


def run_evaluation(root: Path, validation_summary: dict | None = None) -> Path:
    paths = load_paths(root)
    linked = pd.read_parquet(paths.linked_path)
    cluster_metrics = cluster_summary(linked)

    labels_path = root / "data/inputs/manual_pair_labels.csv"
    pair_eval = None
    if labels_path.exists():
        labels = pd.read_csv(labels_path)
        pair_eval = pair_metrics(linked, labels)

    save_quality_report(
        output_path=paths.quality_report_path,
        validation_summary=validation_summary or {},
        cluster_metrics=cluster_metrics,
        pair_eval=pair_eval,
    )
    return paths.quality_report_path
