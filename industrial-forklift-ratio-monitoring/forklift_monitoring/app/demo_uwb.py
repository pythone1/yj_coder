from __future__ import annotations

import argparse
import json
from pathlib import Path

from forklift_monitoring.core.config import load_site_config
from forklift_monitoring.uwb.io import load_pdoa_sqlite, load_uwb_csv
from forklift_monitoring.uwb.pipeline import UWBPipeline


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run UWB path counting demo.")
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config" / "site_example.yaml"))
    parser.add_argument("--input", default=str(PROJECT_ROOT / "data" / "sample_uwb_tracks.csv"))
    parser.add_argument("--input-type", choices=["csv", "sqlite"], default="csv")
    args = parser.parse_args()
    config = load_site_config(args.config)
    frames = list(load_pdoa_sqlite(args.input) if args.input_type == "sqlite" else load_uwb_csv(args.input))
    result = UWBPipeline(config).process(frames)
    print("UWB counts:")
    print(json.dumps(result.counts, ensure_ascii=False, indent=2))
    print("Events:")
    for event in result.events:
        print(f"[{event.timestamp_ms}] tag={event.tag_id} path={event.path_name} origin={event.origin} destination={event.destination}")
