# SNA Hybrid PoC Packaging Report

## Delivered components

- Hybrid extraction flow: Databricks SQL + offline sample mode.
- Data validation and profiling checks.
- Location-based `Community_ID` assignment.
- Phased `Sub_Community_ID` linking by work-scope relationship.
- Evaluation artifact generation (`quality_report.json`).

## Reproducible commands

- Full PoC run: `python scripts/run_poc.py --run-all --use-sample-data`
- Databricks run: `python scripts/run_poc.py --run-all` (requires `.env` credentials)

## Output artifacts

- `data/raw/ca_projects_snapshot.parquet`
- `data/interim/validated_projects.parquet`
- `data/interim/community_assignments.parquet`
- `data/outputs/linked_projects.parquet`
- `data/outputs/quality_report.json`

## Known limitations

- Pair-label evaluation currently depends on manual labels in `data/inputs/manual_pair_labels.csv`.
- Similarity model is TF-IDF baseline and should be upgraded to embeddings for production-quality linkage.
- Work-scope normalization is heuristic and will inherit source classification noise.

## Next productionization steps

1. Add embedding model support for project name and description.
2. Add address geocoding fallback for missing coordinates.
3. Add CI (`pytest`, lint, packaging checks) and scheduled orchestration.
4. Add monitoring for distribution drift and threshold health.
