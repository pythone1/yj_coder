from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_MODEL_DIR = next(
    (path for path in ROOT_DIR.iterdir() if path.is_dir() and path.name.startswith("0-")),
    ROOT_DIR / "0-网状污水管网模型",
)
MODEL_DIR = RAW_MODEL_DIR
DATA_DIR = ROOT_DIR / "data" / "generated_0417_scheme_32h_layout_v2"
RESULT_DIR = ROOT_DIR / "results_0417_scheme_32h_layout_v2"
RUNTIME_DIR = ROOT_DIR / "runtime_ascii"
ANALYSIS_DIR = ROOT_DIR / "analysis"
FIGURE_DIR = ANALYSIS_DIR / "figures"

MODEL_1D_INP = MODEL_DIR / "0417_32h_clean_baseline_no_J20_J48_J11.inp"
MODEL_1D_OUT = MODEL_1D_INP.with_suffix(".out")
MODEL_1D_RPT = MODEL_1D_INP.with_suffix(".rpt")

MODEL_2D_INP = MODEL_DIR / "0417_32h_injection_50pct_J20_J48_J11.inp"
MODEL_2D_OUT = MODEL_2D_INP.with_suffix(".out")
MODEL_2D_RPT = MODEL_2D_INP.with_suffix(".rpt")
MODEL_2D_TSB = RAW_MODEL_DIR / "0-网状污水管网（加2维）.2D cells.tsb"

TWOD_NODE_SHP = RAW_MODEL_DIR / "2维点" / "2D Nodes.SHP"
BOUNDARY_SHP = RAW_MODEL_DIR / "gis" / "范围.shp"
DEM_DIR = RAW_MODEL_DIR / "gis" / "dem"

ANALYSIS_SUMMARY_JSON = ANALYSIS_DIR / "0416_模型解析摘要.json"
ANALYSIS_REPORT_MD = ANALYSIS_DIR / "0416_模型解析报告.md"


def _read_section_rows(inp_path: Path, section_name: str) -> list[list[str]]:
    rows: list[list[str]] = []
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
    if not inp_path.exists():
        return tuple()
    return tuple(row[0] for row in _read_section_rows(inp_path, section_name) if row)


def _read_inflow_nodes(inp_path: Path) -> tuple[str, ...]:
    if not inp_path.exists():
        return tuple()
    rows = _read_section_rows(inp_path, "INFLOWS")
    return tuple(row[0] for row in rows if row)


CORE_JUNCTION_NODES = _read_section_names(MODEL_1D_INP, "JUNCTIONS")
OUTFALL_NODES = _read_section_names(MODEL_1D_INP, "OUTFALLS")
DEFAULT_TRUTH_INFLOW_NODES = _read_inflow_nodes(MODEL_2D_INP)

# 0417 方案：20 个候选井、11 个监测点、3 个真值注入点。
# 候选井强制包含真值点，并按管网距离拉开，降低近邻代偿。
CANDIDATE_NODES = (
    "J20", "J48", "J11", "J29", "J31", "J41", "J72", "J86", "J73", "J91",
    "J92", "J90", "J64", "J65", "J10", "J8", "J5", "J30", "J52", "J50",
)
MONITOR_NODES = ("J19", "J24", "J25", "J27", "J46", "J47", "J49", "J84", "J62", "J61", "J9", "J50", "J7", "J75")
TRUTH_INJECTION_NODES = ("J20", "J48", "J11")
OUTFALL_NODE = OUTFALL_NODES[0] if OUTFALL_NODES else "J6"
TERMINAL_NODE = OUTFALL_NODE

# 0417 v2 方案按 5 分钟采样，模型总时长缩短为 32 小时。
STEP_MINUTES = 5
STEP_SECONDS = STEP_MINUTES * 60

BASELINE_MODEL_INP = MODEL_1D_INP
BASELINE_MODEL_OUT = MODEL_1D_OUT
BASELINE_MODEL_RPT = MODEL_1D_RPT

# 事件模型为 J20/J48/J11 三点 50% 注水模型。
TRUTH_EVENT_MODEL_INP = MODEL_2D_INP
TRUTH_EVENT_MODEL_OUT = MODEL_2D_OUT
TRUTH_EVENT_MODEL_RPT = MODEL_2D_RPT

TOTAL_PROCESS_CSV = DATA_DIR / "0417_总入流过程_5分钟.csv"
TRUTH_INJECTION_CSV = DATA_DIR / "0417_真值注水数据_5分钟.csv"
BASELINE_MONITOR_CSV = DATA_DIR / "0417_基线监测_5分钟.csv"
EVENT_MONITOR_CSV = DATA_DIR / "0417_事件监测_5分钟.csv"
OBSERVED_DELTA_CSV = DATA_DIR / "0417_观测增量_5分钟.csv"
OUTLET_SERIES_CSV = DATA_DIR / "0417_排口过程_5分钟.csv"
DATA_SUMMARY_JSON = DATA_DIR / "0417_数据构造汇总.json"

SMALL_RESULT_DIR = RESULT_DIR / "small_run"
ASCII_BASELINE_TEMPLATE = RUNTIME_DIR / "baseline_template.inp"


@dataclass(frozen=True)
class ExperimentConfig:
    ga_population_count: int = 3
    ga_population_size: int = 20
    ga_generations: int = 6
    ga_elite_ratio: float = 0.15
    ga_mutation_strength: float = 0.18
    ga_migration_interval: int = 3
    ga_migration_count: int = 1
    ga_competition_replace_count: int = 1
    ga_dedup_decimals: int = 5
    am_chain_count: int = 4
    am_samples_per_chain: int = 160
    am_warmup: int = 40
    am_adapt_start: int = 40
    am_initial_covariance: float = 0.002
    am_eps: float = 1e-8
    initial_ppd_keep_fraction: float = 0.75
    initial_ppd_min_count: int = 30
    initial_ppd_min_mean_nse: float = -100.0
    initial_ppd_max_nse_drop: float = 0.50
    initial_ppd_rank_pressure: float = 1.5
    am_start_weighted: bool = True
    am_use_prior_in_acceptance: bool = False
    am_use_initial_ppd_covariance: bool = True
    am_prior_kernel_scale: float = 0.01
    am_proposal_method: str = "tangent_projected_gaussian"
    posterior_validation_samples: int = 24
    parallel_workers: int = 4
    random_seed: int = 20260416
    progress_step_interval: int = 10


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    SMALL_RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)


def runtime_model_path(worker_id: int) -> Path:
    worker_dir = RUNTIME_DIR / f"worker_{worker_id}"
    worker_dir.mkdir(parents=True, exist_ok=True)
    target = worker_dir / "model.inp"
    # Always refresh from the clean baseline before injecting a candidate.
    # This prevents stale worker INPs from older schemes or failed runs from
    # silently carrying old INFLOWS/TIMESERIES into a new evaluation.
    target.write_bytes(BASELINE_MODEL_INP.read_bytes())
    return target
