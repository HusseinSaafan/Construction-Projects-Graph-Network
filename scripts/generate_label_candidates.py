from __future__ import annotations

from itertools import combinations
from pathlib import Path
import random

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MAX_ROWS = 500
PER_SCOPE_TARGET = 125
RANDOM_SEED = 42


def normalize_scope(scope: str) -> str:
    text = (scope or "").strip().lower()
    if "new construction" in text:
        return "new"
    if "maintenance" in text:
        return "maintenance"
    if "renovation" in text or "alteration" in text:
        return "renovation"
    return "other"


def scope_pair_name(scope_a: str, scope_b: str) -> str:
    pair = {scope_a, scope_b}
    if scope_a == "maintenance" and scope_b == "maintenance":
        return "maintenance_maintenance"
    if pair == {"maintenance", "new"}:
        return "maintenance_to_new"
    if "renovation" in pair and "maintenance" in pair:
        return "renovation_maintenance"
    return "new_construction"


def build_pairs(df: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    grouped = df.groupby("Community_ID", sort=False)
    for _, cdf in grouped:
        if len(cdf) < 2:
            continue
        records = cdf.to_dict("records")
        for a, b in combinations(records, 2):
            sa, sb = a["scope_group"], b["scope_group"]
            pair_name = scope_pair_name(sa, sb)
            rows.append(
                {
                    "project_id_a": str(a["PROJECT_ID"]),
                    "project_id_b": str(b["PROJECT_ID"]),
                    "scope_pair": pair_name,
                    "scope_a": sa,
                    "scope_b": sb,
                    "community_id_a": a["Community_ID"],
                    "community_id_b": b["Community_ID"],
                    "project_name_a": a["PROJECT_NAME"],
                    "project_name_b": b["PROJECT_NAME"],
                    "project_description_a": a["PROJECT_DESCRIPTION"],
                    "project_description_b": b["PROJECT_DESCRIPTION"],
                    "completion_date_a": a["PROJECT_ESTIMATED_COMPLETION_DATE"],
                    "completion_date_b": b["PROJECT_ESTIMATED_COMPLETION_DATE"],
                    "latitude_a": a["PROJECT_LATITUDE"],
                    "longitude_a": a["PROJECT_LONGITUDE"],
                    "latitude_b": b["PROJECT_LATITUDE"],
                    "longitude_b": b["PROJECT_LONGITUDE"],
                    "same_project": "",
                    "review_notes": "",
                }
            )
    return rows


def main() -> None:
    random.seed(RANDOM_SEED)
    source_path = ROOT / "data/interim/community_assignments.parquet"
    output_path = ROOT / "data/inputs/manual_pair_labels_candidates.csv"

    df = pd.read_parquet(source_path)
    df["scope_group"] = df["PREDICTED_PROJECT_WORK_SCOPE"].astype(str).map(normalize_scope)
    df["PROJECT_ESTIMATED_COMPLETION_DATE"] = pd.to_datetime(
        df["PROJECT_ESTIMATED_COMPLETION_DATE"], errors="coerce"
    ).dt.date

    all_pairs = pd.DataFrame(build_pairs(df))
    if all_pairs.empty:
        raise RuntimeError("No candidate pairs found. Check community assignments.")

    selected_frames = []
    for scope_pair in [
        "new_construction",
        "maintenance_to_new",
        "renovation_maintenance",
        "maintenance_maintenance",
    ]:
        subset = all_pairs[all_pairs["scope_pair"] == scope_pair]
        if subset.empty:
            continue
        n = min(PER_SCOPE_TARGET, len(subset))
        selected_frames.append(subset.sample(n=n, random_state=RANDOM_SEED))

    selected = pd.concat(selected_frames, ignore_index=True) if selected_frames else all_pairs.head(0)

    if len(selected) < MAX_ROWS:
        used = set(zip(selected["project_id_a"], selected["project_id_b"]))
        remaining = all_pairs[
            ~all_pairs.apply(lambda r: (r["project_id_a"], r["project_id_b"]) in used, axis=1)
        ]
        add_n = min(MAX_ROWS - len(selected), len(remaining))
        if add_n > 0:
            selected = pd.concat(
                [selected, remaining.sample(n=add_n, random_state=RANDOM_SEED)],
                ignore_index=True,
            )

    selected = selected.head(MAX_ROWS).sort_values(["scope_pair", "community_id_a"]).reset_index(drop=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    selected.to_csv(output_path, index=False)

    print(f"wrote: {output_path}")
    print(f"rows: {len(selected)}")
    print("scope_pair_counts:")
    print(selected["scope_pair"].value_counts().to_string())


if __name__ == "__main__":
    main()
