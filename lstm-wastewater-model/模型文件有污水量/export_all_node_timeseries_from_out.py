from pathlib import Path
import shutil
import pandas as pd
from pyswmm import Output
from swmm.toolkit.shared_enum import NodeAttribute
import os


WORKDIR = Path(r"E:\PY\LSTM\模型文件有污水量")
EXPORT_DIR = WORKDIR / "节点时序导出"
EXPORT_DIR.mkdir(exist_ok=True)

FILES = [
    {
        "label": "有雨水量版",
        "source": WORKDIR / "盱眙污水管3（入渗点有雨水量）.out",
        "temp_ascii": WORKDIR / "model_with_rain.out",
    },
    {
        "label": "无雨水量版",
        "source": WORKDIR / "盱眙污水管3（入渗点无雨水量）.out",
        "temp_ascii": WORKDIR / "model_no_rain.out",
    },
]


ATTRS = [
    ("水深(m)", NodeAttribute.INVERT_DEPTH),
    ("水力水头(m)", NodeAttribute.HYDRAULIC_HEAD),
    ("节点贮水量", NodeAttribute.PONDED_VOLUME),
    ("侧向流量", NodeAttribute.LATERAL_INFLOW),
    ("总入流量", NodeAttribute.TOTAL_INFLOW),
    ("溢流损失", NodeAttribute.FLOODING_LOSSES),
]


def prepare_ascii_copy(src: Path, dst: Path) -> Path:
    try:
        shutil.copyfile(src, dst)
        return dst
    except Exception:
        return src


def export_one(file_info):
    label = file_info["label"]
    src = file_info["source"]
    temp = file_info["temp_ascii"]
    read_path = prepare_ascii_copy(src, temp)
    read_dir = Path(read_path).parent
    read_name = Path(read_path).name

    long_rows = []
    wide_frames = []

    old_cwd = os.getcwd()
    os.chdir(str(read_dir))
    try:
        with Output(read_name) as out:
            nodes = list(out.nodes)
            for node_name in nodes:
                node_df = None
                for col_name, attr in ATTRS:
                    series_dict = out.node_series(node_name, attr)
                    s = pd.Series(series_dict, name=col_name)
                    if node_df is None:
                        node_df = s.to_frame()
                    else:
                        node_df = node_df.join(s, how="outer")

                node_df = node_df.reset_index().rename(columns={"index": "时间"})
                node_df.insert(0, "节点名称", node_name)
                node_df.insert(0, "模型版本", label)
                wide_frames.append(node_df)

                node_long = node_df.melt(
                    id_vars=["模型版本", "节点名称", "时间"],
                    value_vars=[name for name, _ in ATTRS],
                    var_name="结果指标",
                    value_name="数值",
                )
                long_rows.append(node_long)

            node_names_df = pd.DataFrame({"模型版本": label, "节点名称": nodes})
            overview_df = pd.DataFrame(
                [
                    {
                        "模型版本": label,
                        "节点数量": len(nodes),
                        "时序点数_每节点": int(len(wide_frames[0])) if wide_frames else 0,
                        "开始时间": wide_frames[0]["时间"].min() if wide_frames else None,
                        "结束时间": wide_frames[0]["时间"].max() if wide_frames else None,
                        "时间分辨率": "1小时",
                    }
                ]
            )
    finally:
        os.chdir(old_cwd)

    wide_df = pd.concat(wide_frames, ignore_index=True)
    long_df = pd.concat(long_rows, ignore_index=True)

    stats_df = (
        long_df.groupby(["模型版本", "节点名称", "结果指标"], as_index=False)
        .agg(
            最小值=("数值", "min"),
            最大值=("数值", "max"),
            平均值=("数值", "mean"),
            时序点数=("数值", "count"),
        )
    )

    prefix = EXPORT_DIR / f"{label}_全部节点时序"
    wide_df.to_csv(f"{prefix}_宽表.csv", index=False, encoding="utf-8-sig")
    long_df.to_csv(f"{prefix}_长表.csv", index=False, encoding="utf-8-sig")
    stats_df.to_csv(f"{prefix}_统计.csv", index=False, encoding="utf-8-sig")

    with pd.ExcelWriter(f"{prefix}.xlsx", engine="openpyxl") as writer:
        overview_df.to_excel(writer, sheet_name="说明", index=False)
        node_names_df.to_excel(writer, sheet_name="节点清单", index=False)
        wide_df.to_excel(writer, sheet_name="全部节点时序_宽表", index=False)
        long_df.to_excel(writer, sheet_name="全部节点时序_长表", index=False)
        stats_df.to_excel(writer, sheet_name="节点结果统计", index=False)

    return {
        "模型版本": label,
        "节点数量": len(nodes),
        "每节点时序点数": int(len(wide_frames[0])) if wide_frames else 0,
        "输出Excel": f"{prefix}.xlsx",
    }


def main():
    summary = []
    for file_info in FILES:
        try:
            summary.append(export_one(file_info))
        except Exception as e:
            summary.append(
                {
                    "模型版本": file_info["label"],
                    "节点数量": "",
                    "每节点时序点数": "",
                    "输出Excel": f"导出失败: {repr(e)}",
                }
            )
    summary_df = pd.DataFrame(summary)
    summary_df.to_csv(EXPORT_DIR / "导出结果总览.csv", index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(EXPORT_DIR / "全部节点时序导出汇总.xlsx", engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="导出总览", index=False)
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
