from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from forklift_monitoring.uwb.io import load_uwb_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate serial coordinate output from a CSV.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--interval-ms", type=int, default=100)
    args = parser.parse_args()

    for frame in load_uwb_csv(args.input):
        print(f"{frame.timestamp_ms},{frame.tag_id},{frame.x},{frame.y},{frame.z},{frame.quality}", flush=True)
        time.sleep(args.interval_ms / 1000.0)


if __name__ == "__main__":
    main()
