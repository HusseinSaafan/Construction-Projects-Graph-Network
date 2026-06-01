from __future__ import annotations

from pathlib import Path
import shutil
import sys

import pandas as pd


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    source_dataset = root / "project_linking_dataset.csv"
    source_fields = root / "sna_fields_description.csv"

    if not source_dataset.exists():
        raise FileNotFoundError(f"Missing dataset file: {source_dataset}")
    if not source_fields.exists():
        raise FileNotFoundError(f"Missing field description file: {source_fields}")

    raw_target = root / "data/raw/ca_projects_snapshot.parquet"
    fields_target = root / "data/inputs/sna_fields_description.csv"
    raw_target.parent.mkdir(parents=True, exist_ok=True)
    fields_target.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(source_dataset)
    df.to_parquet(raw_target, index=False)
    shutil.copy2(source_fields, fields_target)

    print(f"saved dataset parquet: {raw_target}")
    print(f"saved fields description: {fields_target}")
    print(f"row_count: {len(df)}")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    main()
