from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sna_linking.pipeline import run_communities, run_extract, run_subcommunities, run_validate


def test_pipeline_smoke() -> None:
    run_extract(ROOT, use_sample_data=True)
    run_validate(ROOT)
    run_communities(ROOT, radius_meters=200.0)
    linked = run_subcommunities(ROOT)
    assert linked.exists()
