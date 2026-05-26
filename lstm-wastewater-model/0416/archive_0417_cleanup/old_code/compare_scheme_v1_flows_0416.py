from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(r"E:\PY\LSTM\0416")
DATA_DIR = ROOT / "data" / "generated"
ANALYSIS_DIR = ROOT / "analysis" / "scheme_v1"
FIG_DIR = ANALYSIS_DIR / "figures"

TOTAL_PROCESS_CSV = DATA_DIR / "0416_总入流过程_5分钟.csv"
TRUTH_INJECTION_CSV = DATA_DIR / "0416_真值注水数据_5分钟.csv"
BASELINE_MONITOR_CSV = DATA_DIR / "0416_基线监测_5分钟.csv"
EVENT_MONITOR_CSV = DATA_DIR / "0416_事件监测_5分钟.csv"
OUTLET_CSV = DATA_DIR / "0416_排口过程_5分钟.csv"

SUMMARY_JSON = ANALYSIS_DIR / "0416_scheme_v1_flow_comparison_summary.json"
COMPARISON_CSV = ANALYSIS_DIR / "0416_scheme_v1_flow_comparison_5min.csv"
FIG_FLOW_COMPARE = FIG_DIR / "0416_方案V1_无入流基线与有入流总流量对比.png"


plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "SimSun", "FangSong", "KaiTi"]
plt.rcParams["axes.unicode_minus"] = False


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    total_process = pd.read_csv(TOTAL_PROCESS_CSV, encoding="utf-8-sig")
    truth_injection = pd.read_csv(TRUTH_INJECTION_CSV, encoding="utf-8-sig")
    baseline_monitor = pd.read_csv(BASELINE_MONITOR_CSV, encoding="utf-8-sig")
    event_monitor = pd.read_csv(EVENT_MONITOR_CSV, encoding="utf-8-sig")
    outlet = pd.read_csv(OUTLET_CSV, encoding="utf-8-sig")

    monitor_nodes = [c for c in baseline_monitor.columns if c.startswith("J")]
    event_monitor = event_monitor.iloc[: len(total_process)].copy()
    baseline_monitor = baseline_monitor.iloc[: len(total_process)].copy()
    outlet = outlet.iloc[: len(total_process)].copy()

    comparison = pd.DataFrame(
        {
            "relative_hour": total_process["relative_hour"].to_numpy(dtype=float),
            "baseline_total_inflow_cms": 0.0,
            "event_total_injection_cms": total_process["total_flow_cms"].to_numpy(dtype=float),
            "event_outfall_flow_cms": outlet["outfall_link_flow_cms"].to_numpy(dtype=float),
            "baseline_monitor_max_cms": baseline_monitor[monitor_nodes].max(axis=1).to_numpy(dtype=float),
            "event_monitor_max_cms": event_monitor[monitor_nodes].max(axis=1).to_numpy(dtype=float),
        }
    )
    comparison.to_csv(COMPARISON_CSV, index=False, encoding="utf-8-sig")

    peak_injection = comparison.loc[comparison["event_total_injection_cms"].idxmax()]
    peak_outfall = comparison.loc[comparison["event_outfall_flow_cms"].idxmax()]
    peak_monitor = comparison.loc[comparison["event_monitor_max_cms"].idxmax()]
    summary = {
        "time_scale": {
            "ga_am_data_step_minutes": 5,
            "rows": int(len(total_process)),
            "relative_hour_start": float(total_process["relative_hour"].iloc[0]),
            "relative_hour_end": float(total_process["relative_hour"].iloc[-1]),
            "note": "正式 GA/AM 数据使用 5 分钟采样；方案事件水力响应图另保留 1 分钟输出用于看细节。",
        },
        "baseline_no_inflow": {
            "total_inflow_volume_m3": 0.0,
            "monitor_max_cms": float(comparison["baseline_monitor_max_cms"].max()),
        },
        "event_with_inflow": {
            "total_injection_volume_m3": float(total_process["total_volume_m3"].sum()),
            "peak_total_injection_cms": float(peak_injection["event_total_injection_cms"]),
            "peak_total_injection_hour": float(peak_injection["relative_hour"]),
            "outfall_peak_cms": float(peak_outfall["event_outfall_flow_cms"]),
            "outfall_peak_hour": float(peak_outfall["relative_hour"]),
            "outfall_total_volume_m3": float(outlet["outfall_link_flow_cms"].sum() * 5 * 60),
            "monitor_peak_cms": float(peak_monitor["event_monitor_max_cms"]),
            "monitor_peak_hour": float(peak_monitor["relative_hour"]),
        },
        "per_injection_volume_m3": {
            column.replace("_volume_m3", ""): float(truth_injection[column].sum())
            for column in truth_injection.columns
            if column.endswith("_volume_m3")
        },
        "outputs": {
            "comparison_csv": str(COMPARISON_CSV),
            "figure": str(FIG_FLOW_COMPARE),
        },
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    fig, axes = plt.subplots(3, 1, figsize=(13, 9), dpi=180, sharex=True)
    x = comparison["relative_hour"]

    axes[0].plot(x, comparison["baseline_total_inflow_cms"], lw=1.8, color="#64748b", label="无入流基线：总入流 0")
    axes[0].plot(x, comparison["event_total_injection_cms"], lw=2.2, color="#d97706", label="有入流事件：三点注入总流量")
    axes[0].set_ylabel("流量 CMS")
    axes[0].set_title("无入流基线与有入流事件总注入流量对比")
    axes[0].legend(loc="upper right")
    axes[0].grid(alpha=0.22)

    for column, color in [("J1_flow_cms", "#2563eb"), ("J72_flow_cms", "#dc2626"), ("J49_flow_cms", "#16a34a")]:
        axes[1].plot(truth_injection["relative_hour"], truth_injection[column], lw=1.8, label=column.replace("_flow_cms", ""), color=color)
    axes[1].set_ylabel("流量 CMS")
    axes[1].set_title("三处注入点分项波形")
    axes[1].legend(loc="upper right")
    axes[1].grid(alpha=0.22)

    axes[2].plot(x, comparison["event_outfall_flow_cms"], lw=2.2, color="#0f766e", label="有入流事件：排口流量")
    axes[2].plot(x, comparison["baseline_total_inflow_cms"], lw=1.4, color="#94a3b8", linestyle="--", label="无入流基线：排口/监测流量 0")
    axes[2].set_xlabel("相对时间 h")
    axes[2].set_ylabel("流量 CMS")
    axes[2].set_title("排口响应：有入流事件相对无入流基线的滞后响应")
    axes[2].legend(loc="upper right")
    axes[2].grid(alpha=0.22)

    fig.tight_layout()
    fig.savefig(FIG_FLOW_COMPARE)
    plt.close(fig)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
