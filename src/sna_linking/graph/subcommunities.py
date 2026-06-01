from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass(frozen=True)
class MatchingConfig:
    text_weight: float = 0.80
    date_weight: float = 0.20
    new_construction: float = 0.35
    maintenance_to_new: float = 0.60
    renovation_maintenance: float = 0.45
    maintenance_maintenance: float = 0.68


def _normalize_scope(scope: str) -> str:
    text = (scope or "").strip().lower()
    if "new construction" in text:
        return "new"
    if "maintenance" in text:
        return "maintenance"
    if "renovation" in text or "alteration" in text:
        return "renovation"
    return "other"


def classify_scope_pair(scope_a: str, scope_b: str) -> str:
    pair = {scope_a, scope_b}
    if scope_a == "maintenance" and scope_b == "maintenance":
        return "maintenance_maintenance"
    if pair == {"maintenance", "new"}:
        return "maintenance_to_new"
    if "renovation" in pair and "maintenance" in pair:
        return "renovation_maintenance"
    return "new_construction"


def _pair_similarity(
    row_a: pd.Series,
    row_b: pd.Series,
    text_sim: float,
    text_weight: float,
    date_weight: float,
) -> float:
    date_a = row_a["PROJECT_ESTIMATED_COMPLETION_DATE"]
    date_b = row_b["PROJECT_ESTIMATED_COMPLETION_DATE"]
    day_delta = abs((date_a - date_b).days) if pd.notna(date_a) and pd.notna(date_b) else 365
    date_score = max(0.0, 1.0 - min(day_delta, 365) / 365)
    return text_weight * text_sim + date_weight * date_score


def load_matching_config(config_path: Path | None = None) -> MatchingConfig:
    if config_path is None or not config_path.exists():
        return MatchingConfig()
    payload = json.loads(config_path.read_text())
    return MatchingConfig(
        text_weight=float(payload.get("text_weight", 0.80)),
        date_weight=float(payload.get("date_weight", 0.20)),
        new_construction=float(payload.get("new_construction", 0.35)),
        maintenance_to_new=float(payload.get("maintenance_to_new", 0.60)),
        renovation_maintenance=float(payload.get("renovation_maintenance", 0.45)),
        maintenance_maintenance=float(payload.get("maintenance_maintenance", 0.68)),
    )


def assign_subcommunities(df: pd.DataFrame, config: MatchingConfig | None = None) -> pd.DataFrame:
    if config is None:
        config = MatchingConfig()
    out = df.copy()
    out["scope_group"] = out["PREDICTED_PROJECT_WORK_SCOPE"].map(_normalize_scope)
    out["combined_text"] = (
        out["PROJECT_NAME"].fillna("").astype(str) + " " + out["PROJECT_DESCRIPTION"].fillna("").astype(str)
    )

    sub_ids = {}
    counter = 1
    for community_id, cdf in out.groupby("Community_ID", sort=False):
        idxs = cdf.index.tolist()
        texts = cdf["combined_text"].tolist()
        if len(texts) == 1:
            sub_ids[idxs[0]] = f"{community_id}_S{counter:04d}"
            counter += 1
            continue
        vectors = TfidfVectorizer(stop_words="english").fit_transform(texts)
        sim_matrix = cosine_similarity(vectors)
        local_assigned: list[list[int]] = []
        for local_i, global_i in enumerate(idxs):
            if any(local_i in group for group in local_assigned):
                continue
            group = [local_i]
            scope_i = cdf.iloc[local_i]["scope_group"]
            for local_j in range(local_i + 1, len(idxs)):
                if any(local_j in g for g in local_assigned):
                    continue
                scope_j = cdf.iloc[local_j]["scope_group"]
                pair_name = classify_scope_pair(scope_i, scope_j)
                threshold = getattr(config, pair_name)
                score = _pair_similarity(
                    cdf.iloc[local_i],
                    cdf.iloc[local_j],
                    sim_matrix[local_i, local_j],
                    text_weight=config.text_weight,
                    date_weight=config.date_weight,
                )
                if score >= threshold:
                    group.append(local_j)
            local_assigned.append(group)
            sub_id = f"{community_id}_S{counter:04d}"
            for local_idx in group:
                sub_ids[idxs[local_idx]] = sub_id
            counter += 1

    return out.assign(Sub_Community_ID=out.index.map(sub_ids)).drop(columns=["scope_group", "combined_text"])
