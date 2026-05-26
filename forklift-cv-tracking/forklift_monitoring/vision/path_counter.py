from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from forklift_monitoring.core.geometry import point_in_polygon
from forklift_monitoring.core.types import CameraTrackObservation, PathEvent, Zone


@dataclass
class VisionTripState:
    current_zone: Optional[str] = None
    active_origin: Optional[str] = None
    trip_start_ms: Optional[int] = None


class VisionPathCounter:
    def __init__(self, zones: Dict[str, Zone], min_trip_ms: int = 500) -> None:
        self.zones = zones
        self.min_trip_ms = min_trip_ms
        self.states: Dict[int, VisionTripState] = {}
        self.counts: Dict[str, int] = {}

    def locate_zone(self, obs: CameraTrackObservation) -> Optional[str]:
        point = (obs.center_x, obs.center_y)
        for zone_name, zone in self.zones.items():
            if point_in_polygon(point, zone.polygon):
                return zone_name
        return None

    def update(self, obs: CameraTrackObservation) -> List[PathEvent]:
        zone_name = self.locate_zone(obs)
        state = self.states.setdefault(obs.track_id, VisionTripState())
        events: List[PathEvent] = []
        if zone_name in {"A", "B"} and zone_name != state.current_zone:
            state.active_origin = zone_name
            state.trip_start_ms = obs.timestamp_ms
        if (
            state.active_origin in {"A", "B"}
            and zone_name == "C"
            and state.current_zone != "C"
            and state.trip_start_ms is not None
            and obs.timestamp_ms - state.trip_start_ms >= self.min_trip_ms
        ):
            path_name = f"{state.active_origin}-C"
            self.counts[path_name] = self.counts.get(path_name, 0) + 1
            events.append(PathEvent(timestamp_ms=obs.timestamp_ms, tag_id=f"vision_track_{obs.track_id}", origin=state.active_origin, destination="C", path_name=path_name))
            state.active_origin = None
            state.trip_start_ms = None
        state.current_zone = zone_name
        return events
