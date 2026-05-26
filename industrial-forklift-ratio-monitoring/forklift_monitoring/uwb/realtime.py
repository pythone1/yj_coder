from __future__ import annotations

import csv
import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Optional

import serial

from forklift_monitoring.core.config import SiteConfig
from forklift_monitoring.core.types import SmoothedFrame, UWBFrame
from forklift_monitoring.uwb.pipeline import UWBPipeline


@dataclass
class RealtimeCountUpdate:
    frame: SmoothedFrame
    counts: dict[str, int]
    new_events: list


class RealtimeUWBCounter:
    def __init__(self, config: SiteConfig) -> None:
        self.pipeline = UWBPipeline(config)

    def process_frame(self, frame: UWBFrame) -> RealtimeCountUpdate:
        result = self.pipeline.process([frame])
        return RealtimeCountUpdate(frame=result.frames[-1], counts=result.counts, new_events=result.events)


class SQLiteTailReader:
    def __init__(self, db_path: str | Path, poll_interval: float = 0.2, table_name: str = "location") -> None:
        self.db_path = str(db_path)
        self.poll_interval = poll_interval
        self.table_name = table_name
        self.last_id = 0

    def stream(self) -> Generator[UWBFrame, None, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            while True:
                rows = conn.execute(
                    f"SELECT ID, ts, tagid, x, y, filterX, filterY FROM {self.table_name} WHERE ID > ? ORDER BY ID ASC",
                    (self.last_id,),
                ).fetchall()
                if not rows:
                    time.sleep(self.poll_interval)
                    continue
                for row in rows:
                    self.last_id = row["ID"]
                    x = row["filterX"] if row["filterX"] is not None else row["x"]
                    y = row["filterY"] if row["filterY"] is not None else row["y"]
                    yield UWBFrame(timestamp_ms=_normalize_timestamp_ms(row["ts"]), tag_id=str(row["tagid"]), x=float(x), y=float(y))
        finally:
            conn.close()


class SerialLineReader:
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 0.2, encoding: str = "utf-8") -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.encoding = encoding

    def stream(self) -> Generator[UWBFrame, None, None]:
        ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        try:
            while True:
                raw = ser.readline()
                if not raw:
                    continue
                frame = self._parse_line(raw.decode(self.encoding, errors="ignore").strip())
                if frame is not None:
                    yield frame
        finally:
            ser.close()

    def _parse_line(self, line: str) -> Optional[UWBFrame]:
        if not line:
            return None
        if line.startswith("{"):
            data = json.loads(line)
            return UWBFrame(
                timestamp_ms=int(data["timestamp_ms"]),
                tag_id=str(data["tag_id"]),
                x=float(data["x"]),
                y=float(data["y"]),
                z=float(data.get("z", 0.0)),
                quality=float(data.get("quality", 1.0)),
            )
        row = next(csv.reader([line]))
        if len(row) < 4:
            return None
        timestamp_ms = int(row[0]) if len(row) >= 5 else int(time.time() * 1000)
        tag_id = row[1] if len(row) >= 5 else row[0]
        x = float(row[2] if len(row) >= 5 else row[1])
        y = float(row[3] if len(row) >= 5 else row[2])
        z = float(row[4]) if len(row) >= 6 else 0.0
        quality = float(row[5]) if len(row) >= 6 else 1.0
        return UWBFrame(timestamp_ms=timestamp_ms, tag_id=str(tag_id), x=x, y=y, z=z, quality=quality)


def _normalize_timestamp_ms(value) -> int:
    text = "".join(ch for ch in str(value) if ch.isdigit())
    return int(text[-13:]) if len(text) >= 13 else (int(text) if text else int(time.time() * 1000))
