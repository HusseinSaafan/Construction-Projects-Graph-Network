from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sna_linking.graph.subcommunities import (  # noqa: E402
    MatchingConfig,
    _normalize_scope,
    assign_subcommunities,
    classify_scope_pair,
    load_matching_config,
)
from sna_linking.eval.metrics import pair_metrics  # noqa: E402


GRID = {
    "new_construction": [0.28, 0.32, 0.36, 0.40, 0.44],
    "maintenance_to_new": [0.55, 0.60, 0.65, 0.70],
    "renovation_maintenance": [0.40, 0.45, 0.50, 0.55],
    "maintenance_maintenance": [0.62, 0.68, 0.74],
}


def choose_score(pair_name: str, metrics: dict[str, float]) -> float:
    precision = metrics["pair_precision"]
    recall = metrics["pair_recall"]
    f1 = metrics["pair_f1"]
    if pair_name == "new_construction":
        return recall if precision >= 0.70 else -1.0
    if pair_name == "maintenance_to_new":
        return precision if recall >= 0.35 else -1.0
    if pair_name == "renovation_maintenance":
        return f1
    return precision


def build_scope_pairs(labels: pd.DataFrame, base_df: pd.DataFrame) -> pd.DataFrame:
    id_to_scope = (
        base_df.assign(scope_group=base_df["PREDICTED_PROJECT_WORK_SCOPE"].map(_normalize_scope))
        .astype({"PROJECT_ID": str})[["PROJECT_ID", "scope_group"]]
        .drop_duplicates()
        .set_index("PROJECT_ID")["scope_group"]
        .to_dict()
    )
    out = labels.copy()
    out["project_id_a"] = out["project_id_a"].astype(str)
    out["project_id_b"] = out["project_id_b"].astype(str)
    out["scope_a"] = out["project_id_a"].map(id_to_scope).fillna("other")
    out["scope_b"] = out["project_id_b"].map(id_to_scope).fillna("other")
    out["scope_pair"] = out.apply(lambda r: classify_scope_pair(r["scope_a"], r["scope_b"]), axis=1)
    return out


def main() -> None:
    base_config = load_matching_config(ROOT / "configs/matching_config.json")
    labels = pd.read_csv(ROOT / "data/inputs/manual_pair_labels.csv")
    communities = pd.read_parquet(ROOT / "data/interim/community_assignments.parquet")
    label_ids = set(labels["project_id_a"].astype(str)).union(set(labels["project_id_b"].astype(str)))
    communities = communities[communities["PROJECT_ID"].astype(str).isin(label_ids)].copy()
    labels = build_scope_pairs(labels, communities)

    chosen = {
        "text_weight": base_config.text_weight,
        "date_weight": base_config.date_weight,
        "new_construction": base_config.new_construction,
        "maintenance_to_new": base_config.maintenance_to_new,
        "renovation_maintenance": base_config.renovation_maintenance,
        "maintenance_maintenance": base_config.maintenance_maintenance,
    }
    report: dict[str, dict] = {}

    for pair_name, candidates in GRID.items():
        subset = labels[labels["scope_pair"] == pair_name]
        if subset.empty:
            report[pair_name] = {"status": "skipped_no_labels"}
            continue
        best = {"threshold": chosen[pair_name], "score": -1.0, "metrics": None}
        for threshold in candidates:
            cfg = MatchingConfig(
                text_weight=chosen["text_weight"],
                date_weight=chosen["date_weight"],
                new_construction=chosen["new_construction"],
                maintenance_to_new=chosen["maintenance_to_new"],
                renovation_maintenance=chosen["renovation_maintenance"],
                maintenance_maintenance=chosen["maintenance_maintenance"],
            )
            cfg = MatchingConfig(**{**cfg.__dict__, pair_name: threshold})
            linked = assign_subcommunities(communities, config=cfg)
            m = pair_metrics(linked, subset[["project_id_a", "project_id_b", "same_project"]])
            score = choose_score(pair_name, m)
            if score > best["score"]:
                best = {"threshold": threshold, "score": score, "metrics": m}
        chosen[pair_name] = best["threshold"]
        report[pair_name] = best

    output_config = ROOT / "configs/matching_config.tuned.json"
    output_report = ROOT / "data/outputs/threshold_tuning_report.json"
    output_config.write_text(json.dumps(chosen, indent=2))
    output_report.write_text(json.dumps(report, indent=2))
    print(f"wrote tuned config: {output_config}")
    print(f"wrote tuning report: {output_report}")


if __name__ == "__main__":
    main()
