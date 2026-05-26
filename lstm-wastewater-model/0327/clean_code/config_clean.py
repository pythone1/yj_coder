from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(r"E:\PY\LSTM\0327")
ASCII_DATA_DIR = ROOT_DIR / "data_ascii"
GENERATED_DATA_DIR = ROOT_DIR / "数据" / "生成数据"
RESULT_DIR = ROOT_DIR / "结果"
RUNTIME_DIR = ROOT_DIR / "runtime_data_clean"
INSPECTION_DIR = ROOT_DIR / "export_ascii" / "数据构造"

DRY_BASE_INP = INSPECTION_DIR / "0327_旱天基线模型_10分钟.inp"
TRUTH_EVENT_INP = INSPECTION_DIR / "0327_三点注水模型_10分钟.inp"

TOTAL_PROCESS_CSV = GENERATED_DATA_DIR / "0327_总入流过程_10分钟.csv"
TRUTH_INJECTION_CSV = GENERATED_DATA_DIR / "0327_真值注水数据_10分钟.csv"
BASELINE_MONITOR_CSV = GENERATED_DATA_DIR / "0327_基线监测_10分钟.csv"
EVENT_MONITOR_CSV = GENERATED_DATA_DIR / "0327_事件监测_10分钟.csv"
OBSERVED_DELTA_CSV = GENERATED_DATA_DIR / "0327_观测增量_10分钟.csv"
OUTLET_SERIES_CSV = GENERATED_DATA_DIR / "0327_排口过程_10分钟.csv"

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
MONITOR_NODES = ("J191", "J74", "J78", "J91", "J59", "J123", "J126", "J137", "J145", "J231")
OUTFALL_NODE = "J132"
STEP_SECONDS = 600


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
    am_eps: float = 1e-8
    posterior_validation_samples: int = 12
    parallel_workers: int = 4
    random_seed: int = 20260331
    progress_step_interval: int = 10


def ensure_dirs() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)


def runtime_model_path(worker_id: int) -> Path:
    worker_dir = RUNTIME_DIR / f"worker_{worker_id}"
    worker_dir.mkdir(parents=True, exist_ok=True)
    target = worker_dir / "model.inp"
    if (not target.exists()) or target.stat().st_mtime < DRY_BASE_INP.stat().st_mtime:
        target.write_bytes(DRY_BASE_INP.read_bytes())
    return target


def load_generated_data() -> dict[str, pd.DataFrame]:
    return {
        "total_process": pd.read_csv(TOTAL_PROCESS_CSV, encoding="utf-8-sig"),
        "truth_injection": pd.read_csv(TRUTH_INJECTION_CSV, encoding="utf-8-sig"),
        "baseline_monitor": pd.read_csv(BASELINE_MONITOR_CSV, encoding="utf-8-sig"),
        "event_monitor": pd.read_csv(EVENT_MONITOR_CSV, encoding="utf-8-sig"),
        "observed_delta": pd.read_csv(OBSERVED_DELTA_CSV, encoding="utf-8-sig"),
        "outlet": pd.read_csv(OUTLET_SERIES_CSV, encoding="utf-8-sig"),
    }
