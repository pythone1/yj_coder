"""
项目名称: forklift-monitoring-yolo-uwb
技术领域: 02-computer-vision
模块说明: config.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

from forklift_monitoring.core.types import Zone


@dataclass
class UWBSettings:
    alpha: float
    quality_threshold: float
    min_zone_frames: int
    min_trip_seconds: float


@dataclass
class VisionSettings:
    model: str
    class_ids: List[int]
    class_names: List[str]
    fallback_vehicle_names: List[str]
    confidence: float
    image_size: int
    tracker: str
    lines: Dict[str, Tuple[Tuple[float, float], Tuple[float, float]]]
    zones: Dict[str, Zone]


@dataclass
class FusionSettings:
    assist_window_seconds: float


@dataclass
class SiteConfig:
    site_name: str
    zones: Dict[str, Zone]
    uwb: UWBSettings
    vision: VisionSettings
    fusion: FusionSettings


def load_site_config(path: str | Path) -> SiteConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    zones = {
        name: Zone(name=name, polygon=[tuple(point) for point in zone_raw["polygon"]])
        for name, zone_raw in raw["zones"].items()
    }
    lines = {
        name: (tuple(line_raw["start"]), tuple(line_raw["end"]))
        for name, line_raw in raw["vision"]["lines"].items()
    }
    vision_zones = {
        name: Zone(name=name, polygon=[tuple(point) for point in zone_raw["polygon"]])
        for name, zone_raw in raw["vision"].get("zones", {}).items()
    }

    return SiteConfig(
        site_name=raw["site_name"],
        zones=zones,
        uwb=UWBSettings(
            alpha=raw["uwb"]["smoothing"]["alpha"],
            quality_threshold=raw["uwb"]["quality_threshold"],
            min_zone_frames=raw["uwb"]["min_zone_frames"],
            min_trip_seconds=raw["uwb"]["min_trip_seconds"],
        ),
        vision=VisionSettings(
            model=raw["vision"]["model"],
            class_ids=raw["vision"]["class_ids"],
            class_names=raw["vision"].get("class_names", []),
            fallback_vehicle_names=raw["vision"].get("fallback_vehicle_names", []),
            confidence=raw["vision"]["confidence"],
            image_size=raw["vision"]["image_size"],
            tracker=raw["vision"]["tracker"],
            lines=lines,
            zones=vision_zones,
        ),
        fusion=FusionSettings(assist_window_seconds=raw["fusion"]["assist_window_seconds"]),
    )
