from __future__ import annotations

import argparse
import json
from pathlib import Path

from forklift_monitoring.core.config import load_site_config
from forklift_monitoring.vision.yolo_assist import YoloVisionAssist


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run camera assist counting demo.")
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config" / "site_example.yaml"))
    parser.add_argument("--source", default=0)
    parser.add_argument("--max-frames", type=int, default=300)
    args = parser.parse_args()
    source = int(args.source) if str(args.source).isdigit() else args.source
    result = YoloVisionAssist(load_site_config(args.config)).run(source=source, max_frames=args.max_frames)
    print("Vision counts:")
    print(json.dumps(result.counts, ensure_ascii=False, indent=2))
    print("Vision path counts:")
    print(json.dumps(result.path_counts, ensure_ascii=False, indent=2))
