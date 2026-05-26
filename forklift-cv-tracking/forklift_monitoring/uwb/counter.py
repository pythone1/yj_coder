from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional

from forklift_monitoring.core.geometry import point_in_polygon
from forklift_monitoring.core.types import PathEvent, SmoothedFrame, Zone


@dataclass
class TripState:
    current_zone: Optional[str] = None
    active_origin: Optional[str] = None
    trip_start_ms: Optional[int] = None
    last_completed_at_ms: Optional[int] = None


class UWBPathCounter:
    def __init__(self, zones: Dict[str, Zone], min_trip_seconds: float = 1.0) -> None:
        self.zones = zones
        self.min_trip_ms = int(min_trip_seconds * 1000)
        self.trip_states: Dict[str, TripState] = {}
        self.path_counts: Counter[str] = Counter()

    def locate_zone(self, frame: SmoothedFrame) -> Optional[str]:
        point = (frame.x, frame.y)
        for zone_name, zone in self.zones.items():
            if point_in_polygon(point, zone.polygon):
                return zone_name
        return None

    def update(self, frame: SmoothedFrame) -> List[PathEvent]:
        zone_name = frame.zone_name if frame.zone_name is not None else self.locate_zone(frame)
        frame.zone_name = zone_name
        state = self.trip_states.setdefault(frame.tag_id, TripState())
        events: List[PathEvent] = []

        if zone_name in {"A", "B"} and zone_name != state.current_zone:
            state.active_origin = zone_name
            state.trip_start_ms = frame.timestamp_ms

        if (
            state.active_origin in {"A", "B"}
            and zone_name == "C"
            and state.current_zone != "C"
            and state.trip_start_ms is not None
            and frame.timestamp_ms - state.trip_start_ms >= self.min_trip_ms
        ):
            path_name = f"{state.active_origin}-C"
            self.path_counts[path_name] += 1
            events.append(
                PathEvent(
                    timestamp_ms=frame.timestamp_ms,
                    tag_id=frame.tag_id,
                    origin=state.active_origin,
                    destination="C",
                    path_name=path_name,
                    evidence={"source": "uwb"},
                )
            )
            state.active_origin = None
            state.trip_start_ms = None

        state.current_zone = zone_name
        return events

    def snapshot(self) -> Dict[str, int]:
        return dict(self.path_counts)
