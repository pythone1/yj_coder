# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import subprocess
import zipfile
from pathlib import Path

import pandas as pd
from pyswmm import Output
from swmm.toolkit.shared_enum import LinkAttribute, NodeAttribute


PROJECT_DIR = Path(r"E:\PY\LSTM\0327")
BASE_INP = PROJECT_DIR / "data_ascii" / "dry_base_core.inp"
DATA_DIR = PROJECT_DIR / "数据" / "生成数据"
RESULT_DIR = PROJECT_DIR / "结果"
EXPORT_DIR = RESULT_DIR / "0327_三点注水检查包"
ZIP_PATH = RESULT_DIR / "0327_三点注水检查包.zip"
ASCII_EXPORT_ROOT = PROJECT_DIR / "export_ascii"
ASCII_EXPORT_DIR = ASCII_EXPORT_ROOT / "truth_injection_package"
ASCII_ZIP_PATH = ASCII_EXPORT_ROOT / "truth_injection_package.zip"

TOTAL_PROCESS_CSV = DATA_DIR / "0327_总入流过程_10分钟.csv"
TRUTH_INJECTION_CSV = DATA_DIR / "0327_真值注水数据_10分钟.csv"
BASELINE_MONITOR_CSV = DATA_DIR / "0327_基线监测_10分钟.csv"
EVENT_MONITOR_CSV = DATA_DIR / "0327_事件监测_10分钟.csv"
OBSERVED_DELTA_CSV = DATA_DIR / "0327_观测增量_10分钟.csv"
OUTLET_CSV = DATA_DIR / "0327_排口过程_10分钟.csv"
SCENARIO_JSON = DATA_DIR / "0327_方案.json"

TRUTH_NODES = ("J76", "J124", "J140")
TIMESERIES_MAP = {
    "J76": "TS_J76_0327",
    "J124": "TS_J124_0327",
    "J140": "TS_J140_0327",
}
TERMINAL_NODE = "J231"
TERMINAL_LINK = "C89"


def ensure_export_dir() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    ASCII_EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def load_frames() -> dict[str, pd.DataFrame]:
    return {
        "total_process": pd.read_csv(TOTAL_PROCESS_CSV, encoding="utf-8-sig"),
        "truth_injection": pd.read_csv(TRUTH_INJECTION_CSV, encoding="utf-8-sig"),
        "baseline_monitor": pd.read_csv(BASELINE_MONITOR_CSV, encoding="utf-8-sig"),
        "event_monitor": pd.read_csv(EVENT_MONITOR_CSV, encoding="utf-8-sig"),
        "observed_delta": pd.read_csv(OBSERVED_DELTA_CSV, encoding="utf-8-sig"),
        "outlet": pd.read_csv(OUTLET_CSV, encoding="utf-8-sig"),
    }


def decimal_hour_to_hhmm(rel_hour: float) -> str:
    total_minutes = int(round(rel_hour * 60))
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}"


def build_timeseries_lines(truth_df: pd.DataFrame) -> list[str]:
    lines = [
        ";; 0327 true three-node injection time series (10-minute resolution)",
        ";;Name             Date       Time       Value",
    ]
    for node in TRUTH_NODES:
        series_name = TIMESERIES_MAP[node]
        subset = truth_df[truth_df["节点"] == node].copy().sort_values("步号")
        for _, row in subset.iterrows():
            time_text = decimal_hour_to_hhmm(float(row["相对小时"]))
            value = float(row["注入流量_CMS"])
            lines.append(f"{series_name:<16}            {time_text:<10} {value:.12f}")
    return lines


def build_inflow_lines() -> list[str]:
    lines = [
        ";; 0327 true three-node direct inflows",
        ";;Node             Constituent  Time Series      Type   Mfactor  Sfactor  Baseline",
    ]
    for node in TRUTH_NODES:
        ts_name = TIMESERIES_MAP[node]
        lines.append(f"{node:<16} FLOW         {ts_name:<16} FLOW   1.0      1.0      0.0")
    return lines


def replace_section(lines: list[str], section_name: str, new_body: list[str]) -> list[str]:
    start = None
    end = None
    header = f"[{section_name}]"
    for idx, line in enumerate(lines):
        if line.strip().upper() == header:
            start = idx
            break
    if start is None:
        raise ValueError(f"Section not found: {section_name}")
    for idx in range(start + 1, len(lines)):
        stripped = lines[idx].strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            end = idx
            break
    if end is None:
        end = len(lines)
    return lines[: start + 1] + new_body + [""] + lines[end:]


def append_to_section(lines: list[str], section_name: str, extra_body: list[str]) -> list[str]:
    start = None
    end = None
    header = f"[{section_name}]"
    for idx, line in enumerate(lines):
        if line.strip().upper() == header:
            start = idx
            break
    if start is None:
        raise ValueError(f"Section not found: {section_name}")
    for idx in range(start + 1, len(lines)):
        stripped = lines[idx].strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            end = idx
            break
    if end is None:
        end = len(lines)
    existing = lines[start + 1 : end]
    if existing and existing[-1] != "":
        existing = existing + [""]
    return lines[: start + 1] + existing + extra_body + [""] + lines[end:]


def replace_option_value(lines: list[str], key: str, value: str) -> list[str]:
    updated = []
    for line in lines:
        stripped = line.strip()
        if stripped.upper().startswith(key.upper()):
            updated.append(f"{key:<20} {value}")
        else:
            updated.append(line)
    return updated


def build_export_inp(truth_df: pd.DataFrame) -> Path:
    lines = BASE_INP.read_text(encoding="utf-8", errors="ignore").splitlines()
    lines = replace_option_value(lines, "REPORT_STEP", "00:10:00")
    lines = replace_option_value(lines, "WET_STEP", "00:10:00")
    lines = replace_option_value(lines, "DRY_STEP", "00:10:00")
    lines = replace_section(lines, "INFLOWS", build_inflow_lines())
    lines = append_to_section(lines, "TIMESERIES", build_timeseries_lines(truth_df))

    export_inp = EXPORT_DIR / "0327_三点真值注水方案.inp"
    export_inp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return export_inp


def build_summary_tables(frames: dict[str, pd.DataFrame]) -> dict[str, Path]:
    truth_df = frames["truth_injection"].copy()
    total_df = frames["total_process"].copy()

    truth_df.to_csv(EXPORT_DIR / "0327_三点注水明细.csv", index=False, encoding="utf-8-sig")
    total_df.to_csv(EXPORT_DIR / "0327_总入流过程明细.csv", index=False, encoding="utf-8-sig")
    frames["baseline_monitor"].to_csv(EXPORT_DIR / "0327_基线监测_10分钟.csv", index=False, encoding="utf-8-sig")
    frames["event_monitor"].to_csv(EXPORT_DIR / "0327_事件监测_10分钟.csv", index=False, encoding="utf-8-sig")
    frames["observed_delta"].to_csv(EXPORT_DIR / "0327_观测增量_10分钟.csv", index=False, encoding="utf-8-sig")
    frames["outlet"].to_csv(EXPORT_DIR / "0327_排口过程_10分钟.csv", index=False, encoding="utf-8-sig")

    wide = (
        truth_df.pivot(index=["步号", "相对小时"], columns="节点", values="注入流量_CMS")
        .reset_index()
        .rename_axis(None, axis=1)
        .fillna(0.0)
    )
    wide["三点合计注入流量_CMS"] = wide[list(TRUTH_NODES)].sum(axis=1)
    wide.to_csv(EXPORT_DIR / "0327_三点注水宽表.csv", index=False, encoding="utf-8-sig")

    summary_rows = []
    for node in TRUTH_NODES:
        subset = truth_df[truth_df["节点"] == node].copy().sort_values("步号")
        positive = subset[subset["注入流量_CMS"] > 0]
        summary_rows.append(
            {
                "节点": node,
                "总量_m3": float(subset["该步体积_m3"].sum()),
                "峰值流量_CMS": float(subset["注入流量_CMS"].max()),
                "开始相对小时": float(positive["相对小时"].min()) if not positive.empty else None,
                "结束相对小时": float(positive["相对小时"].max()) if not positive.empty else None,
                "非零步数": int((subset["注入流量_CMS"] > 0).sum()),
            }
        )
    summary_df = pd.DataFrame(summary_rows)
    summary_df.loc[len(summary_df)] = {
        "节点": "TOTAL",
        "总量_m3": float(truth_df["该步体积_m3"].sum()),
        "峰值流量_CMS": float(wide["三点合计注入流量_CMS"].max()),
        "开始相对小时": float(wide.loc[wide["三点合计注入流量_CMS"] > 0, "相对小时"].min()),
        "结束相对小时": float(wide.loc[wide["三点合计注入流量_CMS"] > 0, "相对小时"].max()),
        "非零步数": int((wide["三点合计注入流量_CMS"] > 0).sum()),
    }
    summary_df.to_csv(EXPORT_DIR / "0327_三点注水汇总.csv", index=False, encoding="utf-8-sig")

    manifest = {
        "base_inp": str(BASE_INP),
        "export_inp": str(EXPORT_DIR / "0327_三点真值注水方案.inp"),
        "time_step_seconds": 600,
        "total_duration_hours": 48,
        "injection_duration_hours": 24,
        "waveform_shape": "0-8h rising, 8-16h plateau, 16-24h decay, 24-48h zero",
        "truth_nodes": list(TRUTH_NODES),
        "timeseries_names": TIMESERIES_MAP,
    }
    if SCENARIO_JSON.exists():
        manifest["scenario"] = json.loads(SCENARIO_JSON.read_text(encoding="utf-8"))
    (EXPORT_DIR / "0327_导出场景说明.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    readme = "\n".join(
        [
            "# 0327 三点真值注水检查包",
            "",
            "## 文件说明",
            "",
            "- `0327_三点真值注水方案.inp`: 基于当前 clean baseline 导出的可检查注水模型，只新增三点真值注水时序与 INFLOWS，并把报告步长改为 10 分钟。",
            "- `0327_三点注水明细.csv`: 三个真值节点逐步注水明细表。",
            "- `0327_三点注水宽表.csv`: 以时间步为索引的三节点注水宽表，含三点合计流量。",
            "- `0327_三点注水汇总.csv`: 每个真值节点总量、峰值、起止时段汇总。",
            "- `0327_总入流过程明细.csv`: 当前人工降雨型总注水波形。",
            "- `0327_基线监测_10分钟.csv`: 原始 dry 基线提取并插值后的 10 分钟监测序列。",
            "- `0327_事件监测_10分钟.csv`: 真值注水事件监测序列。",
            "- `0327_观测增量_10分钟.csv`: 事件减基线后的增量序列。",
            "- `0327_排口过程_10分钟.csv`: 排口基线/事件/增量过程。",
            "- `0327_导出场景说明.json`: 场景参数与路径说明。",
            "",
            "## 注水方案",
            "",
            "- 总时长：48 h",
            "- 注水时长：前 24 h",
            "- 时间分辨率：10 min",
            "- 总量：76000 m3",
            "- J76：18000 m3",
            "- J124：26000 m3",
            "- J140：32000 m3",
            "- 波形：0-8 h 上升，8-16 h 峰值平台，16-24 h 衰减到 0，24-48 h 为 0",
            "",
        ]
    )
    (EXPORT_DIR / "README.md").write_text(readme, encoding="utf-8")

    return {
        "truth_detail": EXPORT_DIR / "0327_三点注水明细.csv",
        "truth_wide": EXPORT_DIR / "0327_三点注水宽表.csv",
        "truth_summary": EXPORT_DIR / "0327_三点注水汇总.csv",
        "inp": EXPORT_DIR / "0327_三点真值注水方案.inp",
    }


def validate_export_inp(inp_path: Path) -> dict[str, str]:
    # Validate that the file can at least be opened by PySWMM.
    script = (
        "from pyswmm import Simulation\n"
        f"with Simulation(r'{inp_path}') as sim:\n"
        "    print('OPEN_OK')\n"
        "    print(sim.start_time)\n"
        "    print(sim.end_time)\n"
    )
    result = subprocess.run(
        [r"D:\APP\anaconda\envs\LSTM\python.exe", "-c", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        check=False,
    )
    return {
        "returncode": str(result.returncode),
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def run_export_simulation(ascii_inp: Path) -> dict[str, str]:
    ascii_rpt = ascii_inp.with_suffix(".rpt")
    ascii_out = ascii_inp.with_suffix(".out")
    if ascii_rpt.exists():
        ascii_rpt.unlink()
    if ascii_out.exists():
        ascii_out.unlink()
    script = (
        "from swmm.toolkit import solver\n"
        f"solver.swmm_run(r'{ascii_inp}', r'{ascii_rpt}', r'{ascii_out}')\n"
        "print('RUN_OK')\n"
    )
    result = subprocess.run(
        [r"D:\APP\anaconda\envs\LSTM\python.exe", "-c", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        check=False,
    )
    return {
        "returncode": str(result.returncode),
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "rpt": str(ascii_rpt),
        "out": str(ascii_out),
    }


def extract_terminal_process(ascii_out: Path) -> pd.DataFrame:
    rows = []
    with Output(str(ascii_out)) as out:
        j231_items = list(out.node_series(TERMINAL_NODE, NodeAttribute.TOTAL_INFLOW).items())
        c89_items = list(out.link_series(TERMINAL_LINK, LinkAttribute.FLOW_RATE).items())
    count = min(len(j231_items), len(c89_items))
    if count == 0:
        return pd.DataFrame(columns=["步号", "时间", "相对小时", "J231节点总入流_CMS", "C89连边流量_CMS"])
    zero_time = j231_items[0][0] - (j231_items[1][0] - j231_items[0][0]) if count > 1 else j231_items[0][0]
    for idx in range(count):
        t = j231_items[idx][0]
        rel_hour = (t - zero_time).total_seconds() / 3600.0
        rows.append(
            {
                "步号": idx,
                "时间": str(t),
                "相对小时": float(rel_hour),
                "J231节点总入流_CMS": float(j231_items[idx][1]),
                "C89连边流量_CMS": float(c89_items[idx][1]),
            }
        )
    return pd.DataFrame(rows)


def zip_export_dir() -> None:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(EXPORT_DIR.rglob("*")):
            if path.is_file():
                zf.write(path, arcname=path.relative_to(EXPORT_DIR))


def mirror_to_ascii_dir() -> None:
    if ASCII_EXPORT_DIR.exists():
        for path in sorted(ASCII_EXPORT_DIR.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                try:
                    path.rmdir()
                except OSError:
                    pass
    ASCII_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    for src in sorted(EXPORT_DIR.rglob("*")):
        rel = src.relative_to(EXPORT_DIR)
        dst = ASCII_EXPORT_DIR / rel
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())
    # Add ASCII-friendly aliases for the most important deliverables.
    alias_map = {
        "0327_三点真值注水方案.inp": "truth_injection_model.inp",
        "0327_三点注水明细.csv": "truth_injection_detail.csv",
        "0327_三点注水宽表.csv": "truth_injection_wide.csv",
        "0327_三点注水汇总.csv": "truth_injection_summary.csv",
        "0327_总入流过程明细.csv": "total_inflow_process.csv",
        "0327_导出场景说明.json": "scenario_manifest.json",
        "0327_导出INP校验.json": "inp_validation.json",
    }
    for src_name, alias_name in alias_map.items():
        src = ASCII_EXPORT_DIR / src_name
        if src.exists():
            (ASCII_EXPORT_DIR / alias_name).write_bytes(src.read_bytes())


def zip_ascii_export_dir() -> None:
    if ASCII_ZIP_PATH.exists():
        ASCII_ZIP_PATH.unlink()
    with zipfile.ZipFile(ASCII_ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(ASCII_EXPORT_DIR.rglob("*")):
            if path.is_file():
                zf.write(path, arcname=path.relative_to(ASCII_EXPORT_DIR))


def main() -> None:
    ensure_export_dir()
    frames = load_frames()
    export_inp = build_export_inp(frames["truth_injection"])
    build_summary_tables(frames)
    mirror_to_ascii_dir()
    ascii_export_inp = ASCII_EXPORT_DIR / "truth_injection_model.inp"
    validation = validate_export_inp(ascii_export_inp)
    simulation = run_export_simulation(ascii_export_inp) if validation["returncode"] == "0" else None
    terminal_df = None
    if simulation is not None and simulation["returncode"] == "0":
        ascii_out = Path(simulation["out"])
        ascii_rpt = Path(simulation["rpt"])
        terminal_df = extract_terminal_process(ascii_out)
        terminal_df.to_csv(EXPORT_DIR / "0327_J231_C89出口过程_10分钟.csv", index=False, encoding="utf-8-sig")
        terminal_df.to_csv(ASCII_EXPORT_DIR / "terminal_process_J231_C89.csv", index=False, encoding="utf-8-sig")
        (EXPORT_DIR / "truth_injection_model.out").write_bytes(ascii_out.read_bytes())
        (EXPORT_DIR / "truth_injection_model.rpt").write_bytes(ascii_rpt.read_bytes())
        (EXPORT_DIR / "0327_三点真值注水方案.out").write_bytes(ascii_out.read_bytes())
        (EXPORT_DIR / "0327_三点真值注水方案.rpt").write_bytes(ascii_rpt.read_bytes())
    (EXPORT_DIR / "0327_导出INP校验.json").write_text(
        json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if simulation is not None:
        (EXPORT_DIR / "0327_导出仿真校验.json").write_text(
            json.dumps(simulation, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    zip_export_dir()
    zip_ascii_export_dir()
    print(
        json.dumps(
            {
                "export_dir": str(EXPORT_DIR),
                "zip_path": str(ZIP_PATH),
                "inp_path": str(export_inp),
                "ascii_export_dir": str(ASCII_EXPORT_DIR),
                "ascii_zip_path": str(ASCII_ZIP_PATH),
                "ascii_inp_path": str(ascii_export_inp),
                "validation": validation,
                "simulation": simulation,
                "terminal_rows": 0 if terminal_df is None else int(len(terminal_df)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
