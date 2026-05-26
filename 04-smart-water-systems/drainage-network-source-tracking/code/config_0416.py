"""
项目名称: drainage-network-source-tracking
技术领域: 04-smart-water-systems
模块说明: config_0416.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_MODEL_DIR = ROOT_DIR / "data"
MODEL_DIR = RAW_MODEL_DIR
DATA_DIR = ROOT_DIR / "data" / "generated_0520"
RESULT_DIR = ROOT_DIR / "results_0520"
RUNTIME_DIR = ROOT_DIR / "runtime_ascii"
ANALYSIS_DIR = ROOT_DIR / "analysis_0520"
FIGURE_DIR = ANALYSIS_DIR / "figures"

SOURCE_MODEL_INP = RAW_MODEL_DIR / "0519_新模型.inp"
SOURCE_MODEL_OUT = SOURCE_MODEL_INP.with_suffix(".out")
SOURCE_MODEL_RPT = SOURCE_MODEL_INP.with_suffix(".rpt")

MODEL_1D_INP = RAW_MODEL_DIR / "0520_clean_baseline.inp"
MODEL_1D_OUT = MODEL_1D_INP.with_suffix(".out")
MODEL_1D_RPT = MODEL_1D_INP.with_suffix(".rpt")

MODEL_2D_INP = RAW_MODEL_DIR / "0520_truth_event.inp"
MODEL_2D_OUT = MODEL_2D_INP.with_suffix(".out")
MODEL_2D_RPT = MODEL_2D_INP.with_suffix(".rpt")

BASELINE_MODEL_INP = MODEL_1D_INP
BASELINE_MODEL_OUT = MODEL_1D_OUT
BASELINE_MODEL_RPT = MODEL_1D_RPT
TRUTH_EVENT_MODEL_INP = MODEL_2D_INP
TRUTH_EVENT_MODEL_OUT = MODEL_2D_OUT
TRUTH_EVENT_MODEL_RPT = MODEL_2D_RPT

ANALYSIS_SUMMARY_JSON = ANALYSIS_DIR / "0520_model_analysis_summary.json"
ANALYSIS_REPORT_MD = ANALYSIS_DIR / "0520_model_analysis_report.md"

CANDIDATE_NODES = (
    "10", "62", "124", "42", "178",
    "63", "103", "241", "273", "215",
    "216", "60", "308", "310", "312",
    "118", "304", "64", "91", "85",
)
MONITOR_NODES = ("286", "223", "239", "267", "8", "251", "252", "189", "37")
TRUTH_INJECTION_NODES = ("103", "304", "10", "178", "42")
TRUTH_INJECTION_SHARES = {
    "103": 0.20,
    "304": 0.20,
    "10": 0.20,
    "178": 0.20,
    "42": 0.20,
}

OUTFALL_NODE = "293"
TERMINAL_NODE = OUTFALL_NODE

STEP_MINUTES = 10
STEP_SECONDS = STEP_MINUTES * 60
SIMULATION_HOURS = 36.0

TRUTH_EVENT_START_HOUR = 0.0
TRUTH_EVENT_DURATION_MINUTES = 1440
TRUTH_INJECTION_WAVEFORM_MODE = "0417_50pct_24h_10min"
TRUTH_INJECTION_TOTAL_VOLUME_M3 = 3780.0
TRUTH_INJECTION_VOLUME_RATIO_OF_BASELINE_OUTFALL = 0.0
TRUTH_INJECTION_FALLBACK_TOTAL_VOLUME_M3 = 3780.0

TOTAL_PROCESS_CSV = DATA_DIR / "0520_total_process_10min.csv"
TRUTH_INJECTION_CSV = DATA_DIR / "0520_truth_injection_10min.csv"
BASELINE_MONITOR_CSV = DATA_DIR / "0520_baseline_monitor_10min.csv"
EVENT_MONITOR_CSV = DATA_DIR / "0520_event_monitor_10min.csv"
OBSERVED_DELTA_CSV = DATA_DIR / "0520_observed_delta_10min.csv"
OUTLET_SERIES_CSV = DATA_DIR / "0520_outlet_series_10min.csv"
DATA_SUMMARY_JSON = DATA_DIR / "0520_data_summary.json"

SMALL_RESULT_DIR = RESULT_DIR / "small_run"
ASCII_BASELINE_TEMPLATE = RUNTIME_DIR / "baseline_template.inp"
WORKFLOW_GUIDE_TXT = ROOT_DIR / "0520_workflow_guide.txt"
TRUTH_INJECTION_DESIGN_CSV = ANALYSIS_DIR / "0520_truth_injection_design.csv"
TRUTH_INJECTION_DESIGN_JSON = ANALYSIS_DIR / "0520_truth_injection_design.json"


def _read_section_rows(inp_path: Path, section_name: str) -> list[list[str]]:
    rows: list[list[str]] = []
    if not inp_path.exists():
        return rows
    section = ""
    for raw in inp_path.read_text(encoding="gbk", errors="ignore").splitlines():
        stripped = raw.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1].upper()
            continue
        if section != section_name.upper() or not stripped or stripped.startswith(";"):
            continue
        rows.append(stripped.split())
    return rows


def _read_section_names(inp_path: Path, section_name: str) -> tuple[str, ...]:
    return tuple(row[0] for row in _read_section_rows(inp_path, section_name) if row)


CORE_JUNCTION_NODES = _read_section_names(SOURCE_MODEL_INP, "JUNCTIONS")
OUTFALL_NODES = _read_section_names(SOURCE_MODEL_INP, "OUTFALLS")


@dataclass(frozen=True)
class ExperimentConfig:
    ga_population_count: int = 3
    ga_population_size: int = 24
    ga_generations: int = 8
    ga_elite_ratio: float = 0.12
    ga_mutation_strength: float = 0.22
    ga_migration_interval: int = 3
    ga_migration_count: int = 1
    ga_competition_replace_count: int = 1
    ga_dedup_decimals: int = 4
    am_chain_count: int = 4
    am_samples_per_chain: int = 200
    am_warmup: int = 60
    am_adapt_start: int = 60
    am_initial_covariance: float = 0.0015
    am_eps: float = 1e-8
    initial_ppd_keep_fraction: float = 0.60
    initial_ppd_min_count: int = 30
    initial_ppd_min_mean_nse: float = -100.0
    initial_ppd_max_nse_drop: float = 0.25
    initial_ppd_rank_pressure: float = 2.0
    am_start_weighted: bool = True
    am_use_prior_in_acceptance: bool = False
    am_use_initial_ppd_covariance: bool = True
    am_prior_kernel_scale: float = 0.01
    am_proposal_method: str = "tangent_projected_gaussian"
    posterior_validation_samples: int = 32
    parallel_workers: int = 4
    random_seed: int = 20260520
    progress_step_interval: int = 20


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    SMALL_RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)


def runtime_model_path(worker_id: int, force: bool = False) -> Path:
    worker_dir = RUNTIME_DIR / f"worker_{worker_id}"
    worker_dir.mkdir(parents=True, exist_ok=True)
    target = worker_dir / "model.inp"
    if force or worker_id == 0 or not target.exists():
        target.write_bytes(BASELINE_MODEL_INP.read_bytes())
    return target
