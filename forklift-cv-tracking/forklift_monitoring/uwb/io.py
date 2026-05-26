from __future__ import annotations

import csv
import sqlite3
from pathlib import Path
from typing import Iterable

from forklift_monitoring.core.types import UWBFrame


def load_uwb_csv(path: str | Path) -> Iterable[UWBFrame]:
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield UWBFrame(
                timestamp_ms=int(row["timestamp_ms"]),
                tag_id=row["tag_id"],
                x=float(row["x"]),
                y=float(row["y"]),
                z=float(row.get("z", 0.0) or 0.0),
                quality=float(row.get("quality", 1.0) or 1.0),
            )


def load_pdoa_sqlite(path: str | Path, table_name: str = "location") -> Iterable[UWBFrame]:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"""
            SELECT ts, tagid, seq, rawdegree, rawdis, degree, dis, x, y, filterX, filterY
            FROM {table_name}
            ORDER BY ID ASC
            """
        )
        for row in rows:
            x = row["filterX"] if row["filterX"] is not None else row["x"]
            y = row["filterY"] if row["filterY"] is not None else row["y"]
            yield UWBFrame(
                timestamp_ms=_normalize_timestamp_ms(row["ts"]),
                tag_id=str(row["tagid"]),
                x=float(x or 0.0),
                y=float(y or 0.0),
                meta={
                    "seq": row["seq"],
                    "rawdegree": row["rawdegree"],
                    "rawdis": row["rawdis"],
                    "degree": row["degree"],
                    "dis": row["dis"],
                    "source": "pdoa_sqlite",
                },
            )
    finally:
        conn.close()


def _normalize_timestamp_ms(value) -> int:
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()
    digits = "".join(ch for ch in text if ch.isdigit())
    if digits:
        return int(digits[-13:]) if len(digits) >= 13 else int(digits)
    return 0
