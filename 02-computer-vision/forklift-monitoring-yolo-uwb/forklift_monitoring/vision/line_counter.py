"""
项目名称: forklift-monitoring-yolo-uwb
技术领域: 02-computer-vision
模块说明: line_counter.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

from __future__ import annotations

from collections import Counter
from typing import Dict, List, Tuple

from forklift_monitoring.core.geometry import line_side
from forklift_monitoring.core.types import CameraCountEvent, CameraTrackObservation


class TrackLineCounter:
    def __init__(self, lines: Dict[str, Tuple[Tuple[float, float], Tuple[float, float]]]) -> None:
        self.lines = lines
        self.track_last_side: Dict[tuple[str, int], float] = {}
        self.counts: Counter[str] = Counter()

    def update(self, obs: CameraTrackObservation) -> List[CameraCountEvent]:
        point = (obs.center_x, obs.center_y)
        events: List[CameraCountEvent] = []
        for line_id, (start, end) in self.lines.items():
            side = line_side(point, start, end)
            key = (line_id, obs.track_id)
            previous = self.track_last_side.get(key)
            self.track_last_side[key] = side
            if previous is None or previous == 0 or side == 0:
                continue
            if previous * side < 0:
                direction = "positive_to_negative" if previous > 0 else "negative_to_positive"
                self.counts[line_id] += 1
                events.append(CameraCountEvent(timestamp_ms=obs.timestamp_ms, track_id=obs.track_id, line_id=line_id, direction=direction))
        return events

    def snapshot(self) -> Dict[str, int]:
        return dict(self.counts)
