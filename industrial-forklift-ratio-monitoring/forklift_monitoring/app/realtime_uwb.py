from __future__ import annotations

import argparse
import json
from pathlib import Path

from forklift_monitoring.core.config import load_site_config
from forklift_monitoring.uwb.realtime import RealtimeUWBCounter, SQLiteTailReader, SerialLineReader


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description="Realtime UWB path counting.")
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config" / "site_example.yaml"))
    parser.add_argument("--source-type", choices=["sqlite-tail", "serial-line"], default="serial-line")
    parser.add_argument("--db-path")
    parser.add_argument("--port")
    parser.add_argument("--baudrate", type=int, default=115200)
    args = parser.parse_args()
    config = load_site_config(args.config)
    counter = RealtimeUWBCounter(config)
    if args.source_type == "sqlite-tail":
        if not args.db_path:
            raise SystemExit("--db-path is required for sqlite-tail")
        reader = SQLiteTailReader(args.db_path)
    else:
        if not args.port:
            raise SystemExit("--port is required for serial-line")
        reader = SerialLineReader(args.port, baudrate=args.baudrate)
    for frame in reader.stream():
        update = counter.process_frame(frame)
        for event in update.new_events:
            print(json.dumps({"type": "path_event", "timestamp_ms": event.timestamp_ms, "tag_id": event.tag_id, "path": event.path_name, "counts": update.counts}, ensure_ascii=False))
