from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sna_linking.pipeline import (
    run_communities,
    run_evaluation,
    run_extract,
    run_subcommunities,
    run_validate,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SNA project-linking PoC pipeline.")
    parser.add_argument("--run-all", action="store_true")
    parser.add_argument("--extract", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--communities", action="store_true")
    parser.add_argument("--subcommunities", action="store_true")
    parser.add_argument("--evaluate", action="store_true")
    parser.add_argument("--use-sample-data", action="store_true")
    parser.add_argument("--radius-meters", type=float, default=50.0)
    parser.add_argument("--matching-config", type=str, default="configs/matching_config.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = ROOT

    if args.run_all or args.extract:
        raw_path = run_extract(root, use_sample_data=args.use_sample_data)
        print(f"extract complete: {raw_path}")

    validation_summary = None
    if args.run_all or args.validate:
        validated_path, validation_summary = run_validate(root)
        print(f"validation complete: {validated_path}")

    if args.run_all or args.communities:
        communities_path = run_communities(root, radius_meters=args.radius_meters)
        print(f"communities complete: {communities_path}")

    if args.run_all or args.subcommunities:
        linked_path = run_subcommunities(root, matching_config_path=root / args.matching_config)
        print(f"subcommunities complete: {linked_path}")

    if args.run_all or args.evaluate:
        report_path = run_evaluation(root, validation_summary=validation_summary)
        print(f"evaluation complete: {report_path}")


if __name__ == "__main__":
    main()
