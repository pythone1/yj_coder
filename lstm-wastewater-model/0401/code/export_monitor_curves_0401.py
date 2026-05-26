from __future__ import annotations

import json
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager, rcParams
from pyswmm import Output
from swmm.toolkit.shared_enum import NodeAttribute

from config_0401 import BASELINE_MODEL_OUT, MONITOR_NODES, ROOT_DIR, STEP_SECONDS, TRUTH_EVENT_MODEL_OUT


OUTPUT_DIR = ROOT_DIR / "results" / "monitor_curves"
TMP_DIR = OUTPUT_DIR / "_tmp_ascii"
BASELINE_ASCII_OUT = TMP_DIR / "baseline.out"
EVENT_ASCII_OUT = TMP_DIR / "event.out"
SUMMARY_JSON = OUTPUT_DIR / "0401_监测点曲线汇总.json"
DETAIL_CSV = OUTPUT_DIR / "0401_监测点流量水位明细.csv"


def setup_matplotlib_fonts() -> str:
    candidates = [
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "Source Han Sans SC",
        "Arial Unicode MS",
    ]
    installed = {font.name for font in font_manager.fontManager.ttflist}
    chosen = next((name for name in candidates if name in installed), None)
    if chosen is not None:
        rcParams["font.family"] = chosen
        rcParams["font.sans-serif"] = [chosen]
    rcParams["axes.unicode_minus"] = False
    rcParams["font.size"] = 11
    return chosen or "default"


def ensure_dirs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)


def copy_out_files() -> None:
    shutil.copyfile(BASELINE_MODEL_OUT, BASELINE_ASCII_OUT)
    shutil.copyfile(TRUTH_EVENT_MODEL_OUT, EVENT_ASCII_OUT)


def extract_node_series(out_path: Path, node_name: str) -> pd.DataFrame:
    with Output(str(out_path)) as out:
        inflow_items = list(out.node_series(node_name, NodeAttribute.TOTAL_INFLOW).items())
        depth_items = list(out.node_series(node_name, NodeAttribute.INVERT_DEPTH).items())

    rows = []
    for idx, ((ts, inflow), (_, depth)) in enumerate(zip(inflow_items, depth_items)):
        rel_hour = (idx + 1) * STEP_SECONDS / 3600.0
        rows.append(
            {
                "step": idx,
                "time": ts,
                "relative_hour": rel_hour,
                "flow_cms": float(inflow),
                "depth_m": float(depth),
            }
        )
    return pd.DataFrame(rows)


def build_plot(node_name: str, baseline_df: pd.DataFrame, event_df: pd.DataFrame) -> Path:
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    fig.suptitle(f"{node_name} 监测点流量/水位对比", fontsize=15)

    panels = [
        ("未注水（旱天基线）", baseline_df, axes[0], "#2563eb", "#dc2626"),
        ("注水后（0.3倍事件模板）", event_df, axes[1], "#0f766e", "#b45309"),
    ]

    for title, df, ax, flow_color, depth_color in panels:
        ax.plot(df["relative_hour"], df["flow_cms"], color=flow_color, linewidth=1.8, label="流量 (CMS)")
        ax.set_ylabel("流量 (CMS)", color=flow_color)
        ax.tick_params(axis="y", labelcolor=flow_color, labelsize=10)
        ax.tick_params(axis="x", labelsize=10)
        ax.grid(True, alpha=0.25)
        ax.set_title(title, fontsize=12)

        ax2 = ax.twinx()
        ax2.plot(df["relative_hour"], df["depth_m"], color=depth_color, linewidth=1.4, linestyle="--", label="水位/水深 (m)")
        ax2.set_ylabel("水位/水深 (m)", color=depth_color)
        ax2.tick_params(axis="y", labelcolor=depth_color, labelsize=10)

        lines = ax.get_lines() + ax2.get_lines()
        labels = [line.get_label() for line in lines]
        ax.legend(lines, labels, loc="upper right")

    axes[1].set_xlabel("相对小时")
    fig.tight_layout(rect=[0, 0, 1, 0.97])

    output_path = OUTPUT_DIR / f"{node_name}_监测点流量水位对照.png"
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main() -> None:
    ensure_dirs()
    copy_out_files()
    chosen_font = setup_matplotlib_fonts()

    all_rows = []
    saved_files = []
    for node_name in MONITOR_NODES:
        baseline_df = extract_node_series(BASELINE_ASCII_OUT, node_name)
        baseline_df["scenario"] = "未注水"
        baseline_df["monitor"] = node_name

        event_df = extract_node_series(EVENT_ASCII_OUT, node_name)
        event_df["scenario"] = "注水后"
        event_df["monitor"] = node_name

        all_rows.append(baseline_df)
        all_rows.append(event_df)
        saved_files.append(str(build_plot(node_name, baseline_df, event_df)))

    detail_df = pd.concat(all_rows, ignore_index=True)
    detail_df.to_csv(DETAIL_CSV, index=False, encoding="utf-8-sig")

    summary = {
        "baseline_out": str(BASELINE_MODEL_OUT),
        "event_out": str(TRUTH_EVENT_MODEL_OUT),
        "monitor_count": len(MONITOR_NODES),
        "font": chosen_font,
        "detail_csv": str(DETAIL_CSV),
        "plot_files": saved_files,
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
