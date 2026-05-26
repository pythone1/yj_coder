"""
项目名称: forklift-monitoring-yolo-uwb
技术领域: 02-computer-vision
模块说明: yolo_assist.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Dict, List, Optional

import cv2

from forklift_monitoring.core.config import SiteConfig
from forklift_monitoring.core.types import CameraCountEvent, CameraTrackObservation, PathEvent
from forklift_monitoring.vision.line_counter import TrackLineCounter
from forklift_monitoring.vision.path_counter import VisionPathCounter


@dataclass
class VisionAssistResult:
    events: List[CameraCountEvent]
    counts: Dict[str, int]
    path_events: List[PathEvent]
    path_counts: Dict[str, int]


class YoloVisionAssist:
    def __init__(self, config: SiteConfig) -> None:
        self.config = config
        settings_dir = Path(__file__).resolve().parents[2] / ".ultralytics"
        settings_dir.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("YOLO_CONFIG_DIR", str(settings_dir))
        from ultralytics import YOLO

        self.model = YOLO(config.vision.model)
        self.counter = TrackLineCounter(config.vision.lines)
        self.path_counter = VisionPathCounter(config.vision.zones) if config.vision.zones else None

    def run(self, source: str | int = 0, max_frames: Optional[int] = None) -> VisionAssistResult:
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open source: {source}")
        events: List[CameraCountEvent] = []
        path_events: List[PathEvent] = []
        frame_idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            results = self.model.track(frame, persist=True, conf=self.config.vision.confidence, classes=self.config.vision.class_ids, imgsz=self.config.vision.image_size, tracker=self.config.vision.tracker, verbose=False)
            if results:
                boxes = results[0].boxes
                if boxes is not None and boxes.id is not None:
                    ids = boxes.id.int().cpu().tolist()
                    xyxy = boxes.xyxy.cpu().tolist()
                    confs = boxes.conf.cpu().tolist()
                    classes = boxes.cls.int().cpu().tolist()
                    names = results[0].names
                    timestamp_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))
                    for track_id, box, conf, class_id in zip(ids, xyxy, confs, classes):
                        class_name = names.get(class_id, str(class_id))
                        if not self._is_target_class(class_id, class_name):
                            continue
                        obs = CameraTrackObservation(timestamp_ms=timestamp_ms, track_id=track_id, class_id=class_id, class_name=class_name, center_x=(box[0] + box[2]) / 2.0, center_y=(box[1] + box[3]) / 2.0, confidence=conf)
                        events.extend(self.counter.update(obs))
                        if self.path_counter is not None:
                            path_events.extend(self.path_counter.update(obs))
            frame_idx += 1
            if max_frames is not None and frame_idx >= max_frames:
                break
        cap.release()
        return VisionAssistResult(events=events, counts=self.counter.snapshot(), path_events=path_events, path_counts=self.path_counter.counts if self.path_counter is not None else {})

    def _is_target_class(self, class_id: int, class_name: str) -> bool:
        class_name_lower = class_name.lower()
        if self.config.vision.class_names:
            return class_name_lower in {name.lower() for name in self.config.vision.class_names}
        if self.config.vision.class_ids and class_id in self.config.vision.class_ids:
            if not self.config.vision.fallback_vehicle_names:
                return True
            return any(keyword.lower() in class_name_lower for keyword in self.config.vision.fallback_vehicle_names)
        return any(keyword.lower() in class_name_lower for keyword in self.config.vision.fallback_vehicle_names)
