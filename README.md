# SNA Project Linking Pipeline

Public-safe Python pipeline for project linking using geographic communities and scope-aware sub-community matching.

No private datasets are included in this repository.

## Repository purpose

This project provides a reusable pipeline that:

- Ingests project data (local CSV/parquet or Databricks extraction).
- Validates and profiles required fields.
- Builds location communities (`Community_ID`) from latitude/longitude.
- Builds sub-communities (`Sub_Community_ID`) using TF-IDF text similarity and date similarity.
- Supports threshold tuning by work-scope pair.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Input data requirements

Provide a dataset with these columns:

- `PROJECT_ID`
- `PROJECT_NAME`
- `PROJECT_DESCRIPTION`
- `PROJECT_ESTIMATED_COMPLETION_DATE`
- `PROJECT_LATITUDE`
- `PROJECT_LONGITUDE`
- `PREDICTED_PROJECT_WORK_SCOPE`

Optional metadata file:

- `sna_fields_description.csv`

## Run pipeline

Main command options:

- `python scripts/run_poc.py --validate --communities --subcommunities --evaluate`
- `python scripts/run_poc.py --run-all` (includes extraction step)
- `python scripts/run_poc.py --communities --radius-meters 50`
- `python scripts/run_poc.py --subcommunities --matching-config configs/matching_config.json`

## Useful scripts

- `scripts/ingest_local_inputs.py` - moves root CSV inputs into pipeline data paths.
- `scripts/generate_label_candidates.py` - generates up to 500 candidate pairs for manual labeling.
- `scripts/tune_thresholds.py` - scope-aware threshold sweep from labeled pairs.

## Data directories (structure only)

- `data/raw/`
- `data/interim/`
- `data/outputs/`
- `data/inputs/`

These folders are intentionally empty in GitHub and ignored for privacy.
