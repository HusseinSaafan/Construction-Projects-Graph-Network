from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd


REQUIRED_COLUMNS = [
    "PROJECT_ID",
    "PROJECT_NAME",
    "PROJECT_DESCRIPTION",
    "PROJECT_ESTIMATED_COMPLETION_DATE",
    "PROJECT_LATITUDE",
    "PROJECT_LONGITUDE",
    "PREDICTED_PROJECT_WORK_SCOPE",
]


@dataclass
class QualityProfile:
    record_count: int
    null_counts: dict[str, int]
    unknown_counts: dict[str, int]
    duplicate_project_ids: int
    invalid_latitude_count: int
    invalid_longitude_count: int
    work_scope_distribution: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def ensure_required_columns(df: pd.DataFrame) -> None:
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    ensure_required_columns(df)
    out = df.copy()
    out["PROJECT_LATITUDE"] = pd.to_numeric(out["PROJECT_LATITUDE"], errors="coerce")
    out["PROJECT_LONGITUDE"] = pd.to_numeric(out["PROJECT_LONGITUDE"], errors="coerce")
    out["PROJECT_ESTIMATED_COMPLETION_DATE"] = pd.to_datetime(
        out["PROJECT_ESTIMATED_COMPLETION_DATE"], errors="coerce"
    )
    for col in ["PROJECT_NAME", "PROJECT_DESCRIPTION", "PREDICTED_PROJECT_WORK_SCOPE"]:
        out[col] = out[col].astype(str).str.strip()
    out = out.dropna(subset=["PROJECT_LATITUDE", "PROJECT_LONGITUDE", "PROJECT_ESTIMATED_COMPLETION_DATE"])
    return out


def profile_quality(df: pd.DataFrame) -> QualityProfile:
    ensure_required_columns(df)
    unknown_counts = {}
    for col in ["PROJECT_NAME", "PROJECT_DESCRIPTION", "PREDICTED_PROJECT_WORK_SCOPE"]:
        unknown_counts[col] = int(df[col].astype(str).str.upper().eq("UNKNOWN").sum())
    return QualityProfile(
        record_count=int(len(df)),
        null_counts={col: int(df[col].isna().sum()) for col in REQUIRED_COLUMNS},
        unknown_counts=unknown_counts,
        duplicate_project_ids=int(df["PROJECT_ID"].duplicated().sum()),
        invalid_latitude_count=int((~df["PROJECT_LATITUDE"].between(-90, 90)).sum()),
        invalid_longitude_count=int((~df["PROJECT_LONGITUDE"].between(-180, 180)).sum()),
        work_scope_distribution=df["PREDICTED_PROJECT_WORK_SCOPE"].value_counts(dropna=False).to_dict(),
    )
