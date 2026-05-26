"""
项目名称: forklift-monitoring-yolo-uwb
技术领域: 02-computer-vision
模块说明: types.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

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
