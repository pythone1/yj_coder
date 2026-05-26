from pathlib import Path
import re
import math
import pandas as pd
import matplotlib.pyplot as plt


WORKDIR = Path(r"E:\PY\LSTM\模型文件有污水量")
FILES = [
    WORKDIR / "盱眙污水管3（入渗点无雨水量）.inp",
    WORKDIR / "盱眙污水管3（入渗点有雨水量）.inp",
]
OUTPUT_DIR = WORKDIR / "解析结果"

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def read_sections(path: Path):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    sections = {}
    current = None
    current_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if current is not None:
                sections[current] = current_lines
            current = stripped.strip("[]")
            current_lines = []
        else:
            current_lines.append(line)
    if current is not None:
        sections[current] = current_lines
    return sections


def clean_data_lines(lines):
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith(";"):
            continue
        cleaned.append(line.rstrip("\n"))
    return cleaned


def parse_raingages(lines):
    rows = []
    for line in clean_data_lines(lines):
        parts = re.split(r"\s+", line.strip())
        if len(parts) < 5:
            continue
        row = {
            "雨量站名称": parts[0],
            "格式": parts[1],
            "时间间隔": parts[2],
            "比例系数": parts[3],
            "来源类型": parts[4],
            "来源序列": parts[5] if len(parts) > 5 else "",
        }
        rows.append(row)
    return pd.DataFrame(rows)


def parse_inflows(lines):
    rows = []
    for line in clean_data_lines(lines):
        parts = re.split(r"\s+", line.strip())
        if len(parts) < 4:
            continue
        rows.append(
            {
                "节点名称": parts[0],
                "成分": parts[1],
                "时间序列名称": parts[2],
                "入流类型": parts[3],
                "乘数Mfactor": parts[4] if len(parts) > 4 else "",
                "缩放Sfactor": parts[5] if len(parts) > 5 else "",
                "基线值Baseline": parts[6] if len(parts) > 6 else "",
                "模式Pattern": parts[7] if len(parts) > 7 else "",
            }
        )
    return pd.DataFrame(rows)


def parse_timeseries(lines):
    rows = []
    for line in clean_data_lines(lines):
        parts = [p for p in re.split(r"\s+", line.strip()) if p]
        if len(parts) < 3:
            continue
        if len(parts) == 3:
            name, time_raw, value_raw = parts
            date_raw = ""
        else:
            name, date_raw, time_raw, value_raw = parts[0], parts[1], parts[2], parts[3]
        try:
            value = float(value_raw)
        except ValueError:
            continue
        time_index = None
        try:
            time_index = float(time_raw)
        except ValueError:
            if ":" in time_raw:
                hh, mm = time_raw.split(":")[:2]
                time_index = int(hh) + int(mm) / 60
        rows.append(
            {
                "时间序列名称": name,
                "日期字段": date_raw,
                "时间字段原文": time_raw,
                "时间序号": time_index,
                "数值": value,
            }
        )
    return pd.DataFrame(rows)


def calc_series_stats(ts_df: pd.DataFrame):
    rows = []
    for series_name, group in ts_df.groupby("时间序列名称", sort=True):
        group = group.sort_values("时间序号", kind="mergesort")
        max_value = group["数值"].max()
        nonzero = group[group["数值"] > 0]
        rows.append(
            {
                "时间序列名称": series_name,
                "记录点数": int(group.shape[0]),
                "起始时间序号": group["时间序号"].iloc[0],
                "结束时间序号": group["时间序号"].iloc[-1],
                "最小值": group["数值"].min(),
                "最大值": max_value,
                "峰值出现时间序号": group.loc[group["数值"].idxmax(), "时间序号"],
                "非零点数": int(nonzero.shape[0]),
                "非零持续起点": nonzero["时间序号"].iloc[0] if not nonzero.empty else math.nan,
                "非零持续终点": nonzero["时间序号"].iloc[-1] if not nonzero.empty else math.nan,
            }
        )
    return pd.DataFrame(rows)


def build_usage_table(model_name, inflow_df, raingage_df):
    rows = []
    for _, row in inflow_df.iterrows():
        rows.append(
            {
                "模型版本": model_name,
                "用途类别": "节点注水/外部入流",
                "对象名称": row["节点名称"],
                "时间序列名称": row["时间序列名称"],
                "入流类型": row["入流类型"],
                "备注": "",
            }
        )
    for _, row in raingage_df.iterrows():
        if row["来源类型"].upper() == "TIMESERIES":
            rows.append(
                {
                    "模型版本": model_name,
                    "用途类别": "雨量站引用",
                    "对象名称": row["雨量站名称"],
                    "时间序列名称": row["来源序列"],
                    "入流类型": row["格式"],
                    "备注": "汇水区通过雨量站间接使用该序列",
                }
            )
    return pd.DataFrame(rows)


def make_plot(plot_df: pd.DataFrame, output_path: Path, title: str):
    if plot_df.empty:
        return
    plt.figure(figsize=(12, 7))
    for label, group in plot_df.groupby("曲线名称", sort=False):
        group = group.sort_values("时间序号", kind="mergesort")
        plt.plot(group["时间序号"], group["流量值"], marker="o", linewidth=2, markersize=4, label=label)
    plt.xlabel("时间序号（按 inp 文件原值）")
    plt.ylabel("流量值")
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    all_series_rows = []
    all_usage_rows = []
    all_stats_rows = []
    all_plot_rows = []
    summary_rows = []

    for file_path in FILES:
        sections = read_sections(file_path)
        model_name = file_path.stem
        raingage_df = parse_raingages(sections.get("RAINGAGES", []))
        inflow_df = parse_inflows(sections.get("INFLOWS", []))
        ts_df = parse_timeseries(sections.get("TIMESERIES", []))
        stats_df = calc_series_stats(ts_df)
        usage_df = build_usage_table(model_name, inflow_df, raingage_df)

        ts_export = ts_df.copy()
        ts_export.insert(0, "模型版本", model_name)
        usage_export = usage_df.copy()
        stats_export = stats_df.copy()
        stats_export.insert(0, "模型版本", model_name)

        all_series_rows.append(ts_export)
        all_usage_rows.append(usage_export)
        all_stats_rows.append(stats_export)

        summary_rows.append(
            {
                "模型版本": model_name,
                "时间序列总数": ts_df["时间序列名称"].nunique(),
                "注水点数量": inflow_df.shape[0],
                "雨量站引用序列数量": int((raingage_df["来源类型"].str.upper() == "TIMESERIES").sum()) if not raingage_df.empty else 0,
            }
        )

        if not inflow_df.empty:
            merged = inflow_df.merge(ts_df, on="时间序列名称", how="left")
            merged["模型版本"] = model_name
            merged["曲线名称"] = merged["节点名称"] + " -> " + merged["时间序列名称"]
            merged_plot = merged.rename(columns={"数值": "流量值"})
            all_plot_rows.append(
                merged_plot[
                    ["模型版本", "节点名称", "时间序列名称", "时间序号", "流量值", "曲线名称"]
                ]
            )
            plot_stats = (
                merged_plot.groupby(["模型版本", "节点名称", "时间序列名称"], as_index=False)
                .agg(
                    峰值流量=("流量值", "max"),
                    峰值时间序号=("流量值", lambda s: merged_plot.loc[s.idxmax(), "时间序号"]),
                    非零时段点数=("流量值", lambda s: int((s > 0).sum())),
                    非零起点=("时间序号", lambda s: merged_plot.loc[s.index[merged_plot.loc[s.index, "流量值"] > 0], "时间序号"].iloc[0] if (merged_plot.loc[s.index, "流量值"] > 0).any() else math.nan),
                    非零终点=("时间序号", lambda s: merged_plot.loc[s.index[merged_plot.loc[s.index, "流量值"] > 0], "时间序号"].iloc[-1] if (merged_plot.loc[s.index, "流量值"] > 0).any() else math.nan),
                )
            )
        else:
            plot_stats = pd.DataFrame(columns=["模型版本", "节点名称", "时间序列名称", "峰值流量", "峰值时间序号", "非零时段点数", "非零起点", "非零终点"])

        plot_stats.to_csv(OUTPUT_DIR / f"{model_name}_注水点统计.csv", index=False, encoding="utf-8-sig")

        if not inflow_df.empty:
            make_plot(
                merged_plot[["时间序号", "流量值", "曲线名称"]],
                OUTPUT_DIR / f"{model_name}_注水点-时间-流量.png",
                f"{model_name} 注水点-时间-流量曲线",
            )

        ts_export.to_csv(OUTPUT_DIR / f"{model_name}_时间序列明细.csv", index=False, encoding="utf-8-sig")
        usage_export.to_csv(OUTPUT_DIR / f"{model_name}_时间序列用途表.csv", index=False, encoding="utf-8-sig")
        stats_export.to_csv(OUTPUT_DIR / f"{model_name}_时间序列统计.csv", index=False, encoding="utf-8-sig")

    all_series_df = pd.concat(all_series_rows, ignore_index=True)
    all_usage_df = pd.concat(all_usage_rows, ignore_index=True)
    all_stats_df = pd.concat(all_stats_rows, ignore_index=True)
    summary_df = pd.DataFrame(summary_rows)

    if all_plot_rows:
        all_plot_df = pd.concat(all_plot_rows, ignore_index=True)
        make_plot(
            all_plot_df[["时间序号", "流量值", "曲线名称"]],
            OUTPUT_DIR / "两个模型_注水点-时间-流量_总览.png",
            "两个模型注水点-时间-流量总览",
        )
        all_plot_df.to_csv(OUTPUT_DIR / "两个模型_注水点绘图数据.csv", index=False, encoding="utf-8-sig")
        all_plot_stats = (
            all_plot_df.groupby(["模型版本", "节点名称", "时间序列名称"], as_index=False)
            .agg(
                峰值流量=("流量值", "max"),
                峰值时间序号=("流量值", lambda s: all_plot_df.loc[s.idxmax(), "时间序号"]),
                非零时段点数=("流量值", lambda s: int((s > 0).sum())),
                非零起点=("时间序号", lambda s: all_plot_df.loc[s.index[all_plot_df.loc[s.index, "流量值"] > 0], "时间序号"].iloc[0] if (all_plot_df.loc[s.index, "流量值"] > 0).any() else math.nan),
                非零终点=("时间序号", lambda s: all_plot_df.loc[s.index[all_plot_df.loc[s.index, "流量值"] > 0], "时间序号"].iloc[-1] if (all_plot_df.loc[s.index, "流量值"] > 0).any() else math.nan),
            )
        )
    else:
        all_plot_df = pd.DataFrame()
        all_plot_stats = pd.DataFrame()

    excel_path = OUTPUT_DIR / "两个inp时间序列汇总.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="模型概览", index=False)
        all_usage_df.to_excel(writer, sheet_name="时间序列用途", index=False)
        all_stats_df.to_excel(writer, sheet_name="时间序列统计", index=False)
        all_series_df.to_excel(writer, sheet_name="时间序列明细", index=False)
        if not all_plot_df.empty:
            all_plot_df.to_excel(writer, sheet_name="注水点绘图数据", index=False)
        if not all_plot_stats.empty:
            all_plot_stats.to_excel(writer, sheet_name="注水点统计", index=False)

    summary_df.to_csv(OUTPUT_DIR / "两个inp模型概览.csv", index=False, encoding="utf-8-sig")
    all_usage_df.to_csv(OUTPUT_DIR / "两个inp_时间序列用途汇总.csv", index=False, encoding="utf-8-sig")
    all_stats_df.to_csv(OUTPUT_DIR / "两个inp_时间序列统计汇总.csv", index=False, encoding="utf-8-sig")
    all_series_df.to_csv(OUTPUT_DIR / "两个inp_时间序列明细汇总.csv", index=False, encoding="utf-8-sig")

    print(f"输出目录: {OUTPUT_DIR}")
    print(f"Excel: {excel_path.name}")


if __name__ == "__main__":
    main()
