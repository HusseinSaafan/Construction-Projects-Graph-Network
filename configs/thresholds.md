# Threshold Tuning Guide

Current defaults are implemented in `src/sna_linking/graph/subcommunities.py`:

- `new_construction`: `0.35` (recall-first)
- `maintenance_to_new`: `0.50`
- `renovation_maintenance`: `0.45`
- `maintenance_maintenance`: `0.60` (precision-first)

## Tuning workflow

1. Update thresholds in `PhaseThresholds`.
2. Re-run:
   - `python scripts/run_poc.py --run-all --use-sample-data`
3. Inspect `data/outputs/quality_report.json`:
   - maximize pair F1 for balanced mode
   - optimize precision for maintenance-heavy data
   - monitor singleton ratio and cluster count for over/under-linking

## Recommended search order

- Sweep `new_construction` first (largest linkage effect).
- Then tune `maintenance_to_new`.
- Keep `maintenance_maintenance` highest unless recall is too low.
