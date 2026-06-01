from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class DatabricksConfig:
    server_hostname: str
    http_path: str
    access_token: str
    catalog: str
    schema: str
    table: str
    project_state: str


@dataclass(frozen=True)
class PathsConfig:
    root: Path
    raw_path: Path
    validated_path: Path
    community_path: Path
    linked_path: Path
    quality_report_path: Path


def load_databricks_config() -> DatabricksConfig:
    load_dotenv()
    return DatabricksConfig(
        server_hostname=os.getenv("DBX_SERVER_HOSTNAME", ""),
        http_path=os.getenv("DBX_HTTP_PATH", ""),
        access_token=os.getenv("DBX_ACCESS_TOKEN", ""),
        catalog=os.getenv("DBX_CATALOG", "your_catalog"),
        schema=os.getenv("DBX_SCHEMA", "your_schema"),
        table=os.getenv("DBX_TABLE", "your_table"),
        project_state=os.getenv("PROJECT_STATE", "your_state"),
    )


def load_paths(root: Path) -> PathsConfig:
    return PathsConfig(
        root=root,
        raw_path=root / "data/raw/ca_projects_snapshot.parquet",
        validated_path=root / "data/interim/validated_projects.parquet",
        community_path=root / "data/interim/community_assignments.parquet",
        linked_path=root / "data/outputs/linked_projects.parquet",
        quality_report_path=root / "data/outputs/quality_report.json",
    )
