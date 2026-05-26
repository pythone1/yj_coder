from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(r"E:\PY\LSTM\0327")
SOURCE_DIR = Path(r"E:\PY\LSTM\模型文件有污水量\模型文件有污水量")
ASCII_DATA_DIR = PROJECT_DIR / "data_ascii"
CODE_DIR = PROJECT_DIR / "代码"
DATA_DIR = PROJECT_DIR / "数据"
GENERATED_DATA_DIR = DATA_DIR / "生成数据"
RESULT_DIR = PROJECT_DIR / "结果"
RUNTIME_DIR = PROJECT_DIR / "runtime_data"

SOURCE_DRY_INP = SOURCE_DIR / "盱眙污水管3（入渗点无雨水量）.inp"
SOURCE_WET_INP = SOURCE_DIR / "盱眙污水管3（入渗点有雨水量）.inp"

DRY_ORIGINAL_COPY = ASCII_DATA_DIR / "dry_original.inp"
WET_ORIGINAL_COPY = ASCII_DATA_DIR / "wet_original.inp"
DRY_BASE_COPY = ASCII_DATA_DIR / "dry_base_core.inp"
DRY_OUT = ASCII_DATA_DIR / "dry_original.out"
DRY_DB = ASCII_DATA_DIR / "dry_original.db"
DRY_RPT = ASCII_DATA_DIR / "dry_original.rpt"
TIMESERIES_DETAIL_CSV = ASCII_DATA_DIR / "dry_timeseries_detail.csv"

TOTAL_PROCESS_CSV = GENERATED_DATA_DIR / "0327_总入流过程_10分钟.csv"
TRUTH_INJECTION_CSV = GENERATED_DATA_DIR / "0327_真值注水数据_10分钟.csv"
BASELINE_MONITOR_CSV = GENERATED_DATA_DIR / "0327_基线监测_10分钟.csv"
EVENT_MONITOR_CSV = GENERATED_DATA_DIR / "0327_事件监测_10分钟.csv"
OBSERVED_DELTA_CSV = GENERATED_DATA_DIR / "0327_观测增量_10分钟.csv"
OUTLET_SERIES_CSV = GENERATED_DATA_DIR / "0327_排口过程_10分钟.csv"
SCENARIO_JSON = GENERATED_DATA_DIR / "0327_方案.json"

CANDIDATE_NODES = (
    "J193",
    "J70",
    "J71",
    "J74",
    "J76",
    "J78",
    "J81",
    "J85",
    "J89",
    "J41",
    "J120",
    "J124",
    "J125",
    "J129",
    "J131",
    "J135",
    "J137",
    "J140",
    "J145",
    "J67",
)
TRUTH_INJECTION_NODES = ("J76", "J124", "J140")
MONITOR_NODES = ("J191", "J74", "J78", "J91", "J59", "J123", "J126", "J137", "J145", "J231")
OUTFALL_NODE = "J132"
TOTAL_QR_M3 = 76000.0

STEP_SECONDS = 600
TOTAL_HOURS = 48
INJECTION_HOURS = 24
TOTAL_STEPS = int(TOTAL_HOURS * 3600 / STEP_SECONDS)
INJECTION_STEPS = int(INJECTION_HOURS * 3600 / STEP_SECONDS)

TRUTH_TOTAL_VOLUME_M3 = {
    "J76": 18000.0,
    "J124": 26000.0,
    "J140": 32000.0,
}


@dataclass(frozen=True)
class ExperimentConfig:
    ga_population_count: int = 2
    ga_population_size: int = 8
    ga_generations: int = 4
    ga_elite_ratio: float = 0.25
    ga_mutation_strength: float = 0.18
    ga_migration_interval: int = 2
    ga_migration_count: int = 2
    ga_competition_replace_count: int = 2
    am_chain_count: int = 2
    am_samples_per_chain: int = 60
    am_warmup: int = 15
    am_adapt_start: int = 15
    am_initial_covariance: float = 0.002
    am_eps: float = 1.0e-8
    posterior_validation_samples: int = 12
    parallel_workers: int = 4
    random_seed: int = 20260327


def ensure_directories() -> None:
    ASCII_DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)


def copy_original_files_to_ascii_dir() -> None:
    shutil.copyfile(SOURCE_DRY_INP, DRY_ORIGINAL_COPY)
    shutil.copyfile(SOURCE_WET_INP, WET_ORIGINAL_COPY)
    shutil.copyfile(SOURCE_DRY_INP.with_suffix(".out"), DRY_OUT)
    shutil.copyfile(SOURCE_DRY_INP.with_suffix(".db"), DRY_DB)
    shutil.copyfile(SOURCE_DRY_INP.with_suffix(".rpt"), DRY_RPT)


def build_clean_dry_base_copy() -> None:
    original_bytes = DRY_ORIGINAL_COPY.read_bytes()
    lines = original_bytes.splitlines(keepends=True)
    current_section = ""
    kept_lines: list[bytes] = []

    delete_first_token = {
        "JUNCTIONS": {"J197"},
        "OUTFALLS": {"J242"},
        "STORAGE": {"J241"},
        "CONDUITS": {"C90", "C95"},
        "XSECTIONS": {"C90", "C95"},
        "INFLOWS": {"J106", "J197"},
        "COORDINATES": {"J197", "J241", "J242"},
    }
    delete_pair_token = {
        "TAGS": {("Node", "J197"), ("Node", "J241"), ("Node", "J242")},
    }

    for line in lines:
        stripped = line.strip()
        if stripped.startswith(b"[") and stripped.endswith(b"]"):
            current_section = stripped[1:-1].decode("ascii", errors="ignore").upper()
            kept_lines.append(line)
            continue

        if not stripped or stripped.startswith(b";"):
            kept_lines.append(line)
            continue

        tokens = stripped.split()
        if not tokens:
            kept_lines.append(line)
            continue

        first = tokens[0].decode("ascii", errors="ignore")
        if first in delete_first_token.get(current_section, set()):
            continue

        if len(tokens) >= 2:
            pair = (
                tokens[0].decode("ascii", errors="ignore"),
                tokens[1].decode("ascii", errors="ignore"),
            )
            if pair in delete_pair_token.get(current_section, set()):
                continue

        kept_lines.append(line)

    DRY_BASE_COPY.write_bytes(b"".join(kept_lines))


def write_data_manifest(config: ExperimentConfig) -> None:
    payload = {
        "原始旱天文件": str(SOURCE_DRY_INP),
        "原始有雨文件": str(SOURCE_WET_INP),
        "当前有效基线副本": str(DRY_BASE_COPY),
        "当前有效旱天结果out": str(DRY_OUT),
        "候选节点": list(CANDIDATE_NODES),
        "真值注入点": list(TRUTH_INJECTION_NODES),
        "监测点": list(MONITOR_NODES),
        "唯一排口": OUTFALL_NODE,
        "总入流量_QR_m3": TOTAL_QR_M3,
        "总时长小时": TOTAL_HOURS,
        "注入时长小时": INJECTION_HOURS,
        "时间步秒数": STEP_SECONDS,
        "总步数": TOTAL_STEPS,
        "注入步数": INJECTION_STEPS,
        "实验配置": asdict(config),
    }
    (DATA_DIR / "0327_数据口径.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_generated_data() -> dict[str, pd.DataFrame]:
    return {
        "total_process": pd.read_csv(TOTAL_PROCESS_CSV, encoding="utf-8-sig"),
        "truth_injection": pd.read_csv(TRUTH_INJECTION_CSV, encoding="utf-8-sig"),
        "baseline_monitor": pd.read_csv(BASELINE_MONITOR_CSV, encoding="utf-8-sig"),
        "event_monitor": pd.read_csv(EVENT_MONITOR_CSV, encoding="utf-8-sig"),
        "observed_delta": pd.read_csv(OBSERVED_DELTA_CSV, encoding="utf-8-sig"),
        "outlet": pd.read_csv(OUTLET_SERIES_CSV, encoding="utf-8-sig"),
    }


def validate_generated_data_exists() -> None:
    missing = []
    for file_path in [
        TOTAL_PROCESS_CSV,
        TRUTH_INJECTION_CSV,
        BASELINE_MONITOR_CSV,
        EVENT_MONITOR_CSV,
        OBSERVED_DELTA_CSV,
        OUTLET_SERIES_CSV,
    ]:
        if not file_path.exists():
            missing.append(str(file_path))
    if missing:
        raise FileNotFoundError("缺少生成数据文件：\n" + "\n".join(missing))


def parse_inp_sections(inp_path: Path) -> dict[str, list[str]]:
    text = inp_path.read_text(encoding="utf-8", errors="ignore")
    sections: dict[str, list[str]] = {}
    current = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            current = stripped[1:-1].upper()
            sections[current] = []
        elif current:
            sections[current].append(line)
    return sections


def build_structure_data(inp_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    sections = parse_inp_sections(inp_path)

    node_rows = []
    for line in sections.get("COORDINATES", []):
        stripped = line.strip()
        if not stripped or stripped.startswith(";"):
            continue
        parts = stripped.split()
        if len(parts) >= 3:
            node_rows.append({"node": parts[0], "x": float(parts[1]), "y": float(parts[2])})
    node_df = pd.DataFrame(node_rows)

    link_rows = []
    for section_name in ("CONDUITS", "PUMPS"):
        for line in sections.get(section_name, []):
            stripped = line.strip()
            if not stripped or stripped.startswith(";"):
                continue
            parts = stripped.split()
            if len(parts) >= 3:
                link_rows.append(
                    {
                        "link": parts[0],
                        "from_node": parts[1],
                        "to_node": parts[2],
                        "section": section_name,
                    }
                )
    link_df = pd.DataFrame(link_rows)
    return node_df, link_df


def runtime_model_path(worker_id: int) -> Path:
    worker_dir = RUNTIME_DIR / f"worker_{worker_id}"
    worker_dir.mkdir(parents=True, exist_ok=True)
    target = worker_dir / "model.inp"
    if (not target.exists()) or target.stat().st_mtime < DRY_BASE_COPY.stat().st_mtime:
        shutil.copyfile(DRY_BASE_COPY, target)
    return target


# Chinese aliases for compatibility with existing scripts.
项目目录 = PROJECT_DIR
原始目录 = SOURCE_DIR
解析目录 = ASCII_DATA_DIR
代码目录 = CODE_DIR
数据目录 = DATA_DIR
生成数据目录 = GENERATED_DATA_DIR
结果目录 = RESULT_DIR
运行目录 = RUNTIME_DIR
原始旱天文件 = SOURCE_DRY_INP
原始有雨文件 = SOURCE_WET_INP
旱天原始副本 = DRY_ORIGINAL_COPY
雨天原始副本 = WET_ORIGINAL_COPY
基线副本 = DRY_BASE_COPY
旱天结果库 = DRY_OUT
旱天结果汇总库 = DRY_DB
旱天报告文件 = DRY_RPT
时间序列明细文件 = TIMESERIES_DETAIL_CSV
总入流过程文件 = TOTAL_PROCESS_CSV
真值注水文件 = TRUTH_INJECTION_CSV
基线监测文件 = BASELINE_MONITOR_CSV
事件监测文件 = EVENT_MONITOR_CSV
观测增量文件 = OBSERVED_DELTA_CSV
排口过程文件 = OUTLET_SERIES_CSV
方案文件 = SCENARIO_JSON
候选节点 = CANDIDATE_NODES
真值注入点 = TRUTH_INJECTION_NODES
监测点 = MONITOR_NODES
唯一排口 = OUTFALL_NODE
总入流量_QR = TOTAL_QR_M3
时间步秒数 = STEP_SECONDS
总时长小时 = TOTAL_HOURS
注入时长小时 = INJECTION_HOURS
总步数 = TOTAL_STEPS
注入步数 = INJECTION_STEPS
真值总量_m3 = TRUTH_TOTAL_VOLUME_M3
实验配置 = ExperimentConfig
确保目录 = ensure_directories
复制原始文件到ASCII目录 = copy_original_files_to_ascii_dir
生成基线副本 = build_clean_dry_base_copy
生成数据口径说明 = write_data_manifest
读取生成数据 = load_generated_data
校验生成数据存在 = validate_generated_data_exists
解析inp分段 = parse_inp_sections
构建结构数据 = build_structure_data
运行时模型路径 = runtime_model_path
