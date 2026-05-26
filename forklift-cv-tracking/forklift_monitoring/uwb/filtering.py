from __future__ import annotations

from collections import defaultdict
from typing import Dict, Tuple

from forklift_monitoring.core.types import SmoothedFrame, UWBFrame


class ExponentialPositionFilter:
    def __init__(self, alpha: float) -> None:
        self.alpha = alpha
        self._state: Dict[str, Tuple[float, float, float]] = {}

    def update(self, frame: UWBFrame) -> SmoothedFrame:
        prev = self._state.get(frame.tag_id)
        if prev is None:
            smoothed = (frame.x, frame.y, frame.z)
        else:
            smoothed = tuple(
                self.alpha * current + (1.0 - self.alpha) * previous
                for current, previous in zip((frame.x, frame.y, frame.z), prev)
            )
        self._state[frame.tag_id] = smoothed
        return SmoothedFrame(
            timestamp_ms=frame.timestamp_ms,
            tag_id=frame.tag_id,
            x=smoothed[0],
            y=smoothed[1],
            z=smoothed[2],
            quality=frame.quality,
            meta=frame.meta,
        )


class StableZoneResolver:
    def __init__(self, min_zone_frames: int) -> None:
        self.min_zone_frames = min_zone_frames
        self._pending: Dict[str, Tuple[str | None, int]] = defaultdict(lambda: (None, 0))
        self._stable_zone: Dict[str, str | None] = {}

    def update(self, tag_id: str, raw_zone_name: str | None) -> str | None:
        pending_zone, count = self._pending[tag_id]
        if raw_zone_name == pending_zone:
            count += 1
        else:
            pending_zone, count = raw_zone_name, 1
        self._pending[tag_id] = (pending_zone, count)
        if count >= self.min_zone_frames:
            self._stable_zone[tag_id] = raw_zone_name
        return self._stable_zone.get(tag_id)
