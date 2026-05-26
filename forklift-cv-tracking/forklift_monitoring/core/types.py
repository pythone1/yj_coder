from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


Point2D = Tuple[float, float]


@dataclass
class Zone:
    name: str
    polygon: List[Point2D]


@dataclass
class UWBFrame:
    timestamp_ms: int
    tag_id: str
    x: float
    y: float
    z: float = 0.0
    quality: float = 1.0
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SmoothedFrame(UWBFrame):
    zone_name: Optional[str] = None


@dataclass
class PathEvent:
    timestamp_ms: int
    tag_id: str
    origin: str
    destination: str
    path_name: str
    evidence: Dict[str, str] = field(default_factory=dict)


@dataclass
class CameraTrackObservation:
    timestamp_ms: int
    track_id: int
    class_id: int
    class_name: str
    center_x: float
    center_y: float
    confidence: float
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CameraCountEvent:
    timestamp_ms: int
    track_id: int
    line_id: str
    direction: str
    source: str = "vision"
