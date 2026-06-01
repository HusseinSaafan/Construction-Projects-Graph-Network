from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from sna_linking.config import DatabricksConfig

QUERY_TEMPLATE = """
SELECT
  PROJECT_ID,
  PROJECT_NAME,
  PROJECT_DESCRIPTION,
  PROJECT_ESTIMATED_COMPLETION_DATE,
  PROJECT_LATITUDE,
  PROJECT_LONGITUDE,
  PREDICTED_PROJECT_WORK_SCOPE
FROM {catalog}.{schema}.{table}
WHERE PROJECT_STATE = '{project_state}'
"""


def build_query(config: DatabricksConfig) -> str:
    return QUERY_TEMPLATE.format(
        catalog=config.catalog,
        schema=config.schema,
        table=config.table,
        project_state=config.project_state,
    )


def extract_from_databricks(config: DatabricksConfig) -> pd.DataFrame:
    if not (config.server_hostname and config.http_path and config.access_token):
        raise ValueError("Databricks credentials are missing in environment variables.")

    from databricks import sql

    with sql.connect(
        server_hostname=config.server_hostname,
        http_path=config.http_path,
        access_token=config.access_token,
    ) as connection:
        return pd.read_sql(build_query(config), connection)


def build_sample_dataframe() -> pd.DataFrame:
    sample_rows: list[dict[str, Any]] = [
        {
            "PROJECT_ID": "EXAMPLE_001",
            "PROJECT_NAME": "Example Project Alpha",
            "PROJECT_DESCRIPTION": "Example description for demo construction project.",
            "PROJECT_ESTIMATED_COMPLETION_DATE": "2027-01-15",
            "PROJECT_LATITUDE": 34.0500,
            "PROJECT_LONGITUDE": -118.2500,
            "PREDICTED_PROJECT_WORK_SCOPE": "New Construction",
        },
        {
            "PROJECT_ID": "EXAMPLE_002",
            "PROJECT_NAME": "Example Project Alpha Phase 2",
            "PROJECT_DESCRIPTION": "Follow-up scope for the same location cluster.",
            "PROJECT_ESTIMATED_COMPLETION_DATE": "2027-03-01",
            "PROJECT_LATITUDE": 34.0502,
            "PROJECT_LONGITUDE": -118.2498,
            "PREDICTED_PROJECT_WORK_SCOPE": "Maintenance / Service",
        },
        {
            "PROJECT_ID": "EXAMPLE_003",
            "PROJECT_NAME": "Example Project Beta",
            "PROJECT_DESCRIPTION": "Independent renovation effort in another district.",
            "PROJECT_ESTIMATED_COMPLETION_DATE": "2026-09-20",
            "PROJECT_LATITUDE": 40.7127,
            "PROJECT_LONGITUDE": -74.0059,
            "PREDICTED_PROJECT_WORK_SCOPE": "Renovation / Alteration",
        },
        {
            "PROJECT_ID": "EXAMPLE_004",
            "PROJECT_NAME": "Example Project Gamma",
            "PROJECT_DESCRIPTION": "Standalone facilities upgrade project.",
            "PROJECT_ESTIMATED_COMPLETION_DATE": "2026-11-10",
            "PROJECT_LATITUDE": 47.6061,
            "PROJECT_LONGITUDE": -122.3328,
            "PREDICTED_PROJECT_WORK_SCOPE": "New Construction",
        },
    ]
    return pd.DataFrame(sample_rows)


def save_raw_snapshot(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.assign(EXTRACTED_AT=date.today().isoformat()).to_parquet(output_path, index=False)
