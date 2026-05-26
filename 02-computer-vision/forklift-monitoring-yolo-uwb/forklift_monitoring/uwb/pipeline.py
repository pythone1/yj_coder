"""
项目名称: forklift-monitoring-yolo-uwb
技术领域: 02-computer-vision
模块说明: pipeline.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from forklift_monitoring.core.config import SiteConfig
from forklift_monitoring.core.types import PathEvent, SmoothedFrame, UWBFrame
from forklift_monitoring.uwb.counter import UWBPathCounter
from forklift_monitoring.uwb.filtering import ExponentialPositionFilter, StableZoneResolver


@dataclass
class UWBPipelineResult:
    events: List[PathEvent]
    counts: Dict[str, int]
    frames: List[SmoothedFrame]


class UWBPipeline:
    def __init__(self, config: SiteConfig) -> None:
        self.config = config
        self.filter = ExponentialPositionFilter(alpha=config.uwb.alpha)
        self.zone_resolver = StableZoneResolver(min_zone_frames=config.uwb.min_zone_frames)
        self.counter = UWBPathCounter(zones=config.zones, min_trip_seconds=config.uwb.min_trip_seconds)

    def process(self, frames: List[UWBFrame]) -> UWBPipelineResult:
        events: List[PathEvent] = []
        smoothed_frames: List[SmoothedFrame] = []
        for frame in frames:
            if frame.quality < self.config.uwb.quality_threshold:
                continue
            smoothed = self.filter.update(frame)
            raw_zone = self.counter.locate_zone(smoothed)
            smoothed.zone_name = self.zone_resolver.update(smoothed.tag_id, raw_zone)
            events.extend(self.counter.update(smoothed))
            smoothed_frames.append(smoothed)
        return UWBPipelineResult(events=events, counts=self.counter.snapshot(), frames=smoothed_frames)
