from __future__ import annotations

import json
from pathlib import Path

import yaml

from forklift_monitoring.core.config import load_site_config
from forklift_monitoring.uwb.io import load_pdoa_sqlite, load_uwb_csv
from forklift_monitoring.uwb.pipeline import UWBPipeline
from forklift_monitoring.uwb.realtime import RealtimeUWBCounter, SQLiteTailReader, SerialLineReader
from forklift_monitoring.visualization.uwb_report import generate_uwb_report
from forklift_monitoring.vision.yolo_assist import YoloVisionAssist


PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / "project_config.yaml"


def load_project_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def abs_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def run_demo_uwb(project_cfg: dict) -> None:
    site_config = load_site_config(abs_path(project_cfg["run"]["site_config"]))
    uwb_cfg = project_cfg["uwb"]
    input_type = uwb_cfg["input_type"]
    input_path = abs_path(uwb_cfg["input_path"])

    frames = list(load_pdoa_sqlite(input_path) if input_type == "sqlite" else load_uwb_csv(input_path))
    result = UWBPipeline(site_config).process(frames)

    print("UWB counts:")
    print(json.dumps(result.counts, ensure_ascii=False, indent=2))
    print("Events:")
    for event in result.events:
        print(
            f"[{event.timestamp_ms}] tag={event.tag_id} path={event.path_name} "
            f"origin={event.origin} destination={event.destination}"
        )

    vis_cfg = project_cfg.get("visualization", {})
    if vis_cfg.get("enabled", False):
        outputs = generate_uwb_report(
            site_config=site_config,
            result=result,
            output_dir=abs_path(vis_cfg["output_dir"]),
            title="UWB Path Counting Report",
        )
        print("Visualization:")
        print(f"PNG:  {outputs['image']}")
        print(f"HTML: {outputs['html']}")


def run_demo_camera(project_cfg: dict) -> None:
    site_config = load_site_config(abs_path(project_cfg["run"]["site_config"]))
    camera_cfg = project_cfg["camera"]
    source_raw = camera_cfg["source"]
    source = int(source_raw) if str(source_raw).isdigit() else str(source_raw)
    max_frames = int(camera_cfg["max_frames"])

    result = YoloVisionAssist(site_config).run(source=source, max_frames=max_frames)

    print("Vision counts:")
    print(json.dumps(result.counts, ensure_ascii=False, indent=2))
    print("Vision path counts:")
    print(json.dumps(result.path_counts, ensure_ascii=False, indent=2))


def run_realtime_uwb(project_cfg: dict) -> None:
    site_config = load_site_config(abs_path(project_cfg["run"]["site_config"]))
    realtime_cfg = project_cfg["realtime_uwb"]
    counter = RealtimeUWBCounter(site_config)

    source_type = realtime_cfg["source_type"]
    if source_type == "sqlite-tail":
        db_path = str(abs_path(realtime_cfg["db_path"]))
        if not realtime_cfg["db_path"]:
            raise ValueError("realtime_uwb.db_path 不能为空")
        reader = SQLiteTailReader(db_path)
    else:
        port = realtime_cfg["port"]
        baudrate = int(realtime_cfg["baudrate"])
        reader = SerialLineReader(port, baudrate=baudrate)

    print(f"realtime source={source_type}")
    for frame in reader.stream():
        update = counter.process_frame(frame)
        for event in update.new_events:
            print(
                json.dumps(
                    {
                        "type": "path_event",
                        "timestamp_ms": event.timestamp_ms,
                        "tag_id": event.tag_id,
                        "path": event.path_name,
                        "counts": update.counts,
                    },
                    ensure_ascii=False,
                )
            )


def main() -> None:
    project_cfg = load_project_config()
    mode = project_cfg["run"]["mode"]

    if mode == "demo_uwb":
        run_demo_uwb(project_cfg)
    elif mode == "demo_camera":
        run_demo_camera(project_cfg)
    elif mode == "realtime_uwb":
        run_realtime_uwb(project_cfg)
    else:
        raise ValueError(f"不支持的 mode: {mode}")


if __name__ == "__main__":
    main()
