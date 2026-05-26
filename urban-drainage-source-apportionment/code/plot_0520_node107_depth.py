from __future__ import annotations

from pathlib import Path
import shutil

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import pandas as pd
from pyswmm import Output
from swmm.toolkit.shared_enum import NodeAttribute


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
ANALYSIS_DIR = ROOT / "analysis_0520"
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

NODE_ID = "107"
OUT_SRC = max(DATA_DIR.glob("*.out"), key=lambda p: p.stat().st_mtime)
OUT_ASCII = ANALYSIS_DIR / "latest_model_ascii.out"
NODE_TABLE = ANALYSIS_DIR / "0520_all_nodes_full_fields.csv"

PNG_PATH = ANALYSIS_DIR / "0520_node107_depth_ponding_curve.png"
HTML_PATH = ANALYSIS_DIR / "0520_node107_depth_ponding_curve.html"
CSV_PATH = ANALYSIS_DIR / "0520_node107_depth_ponding_timeseries.csv"


def chinese_font() -> FontProperties:
    for path in [
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
    ]:
        if path.exists():
            return FontProperties(fname=str(path))
    return FontProperties()


def main() -> None:
    # swmm-toolkit can fail on Chinese paths, so read from an ASCII copy.
    shutil.copy2(OUT_SRC, OUT_ASCII)

    nodes = pd.read_csv(NODE_TABLE, encoding="utf-8-sig")
    row = nodes[nodes["node"].astype(str) == NODE_ID].iloc[0]
    rim_depth_m = float(row["junction_max_depth_m"])
    rpt_max_depth_m = float(row["rpt_max_depth_m"])
    rpt_reported_max_depth_m = float(row["rpt_reported_max_depth_m"])
    rpt_depth_time_of_max = str(row["rpt_depth_time_of_max"])
    rpt_flood_time_of_max = str(row["rpt_flood_time_of_max"])
    rpt_max_ponded_depth_cm = float(row["rpt_max_ponded_depth_cm"])

    with Output(str(OUT_ASCII)) as out:
        depth = out.node_series(NODE_ID, NodeAttribute.INVERT_DEPTH)
        ponded_volume = out.node_series(NODE_ID, NodeAttribute.PONDED_VOLUME)
        flooding_loss = out.node_series(NODE_ID, NodeAttribute.FLOODING_LOSSES)

    df = pd.DataFrame(
        {
            "time": list(depth.keys()),
            "depth_m": list(depth.values()),
            "ponded_volume_m3": [ponded_volume[t] for t in depth.keys()],
            "flooding_loss_cms": [flooding_loss[t] for t in depth.keys()],
        }
    )
    df["ponded_depth_m"] = (df["depth_m"] - rim_depth_m).clip(lower=0)
    df["ponded_depth_cm"] = df["ponded_depth_m"] * 100
    df["rim_depth_m"] = rim_depth_m
    df["rpt_max_depth_m"] = rpt_max_depth_m
    df["rpt_reported_max_depth_m"] = rpt_reported_max_depth_m
    df["rpt_max_ponded_depth_cm"] = rpt_max_ponded_depth_cm
    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

    peak = df.loc[df["depth_m"].idxmax()]
    pond_peak = df.loc[df["ponded_depth_cm"].idxmax()]
    max_depth_m = float(df["depth_m"].max())
    max_ponded_cm = float(df["ponded_depth_cm"].max())
    reaches_internal_max = abs(max_ponded_cm - rpt_max_ponded_depth_cm) < 1e-3
    reaches_reported_max = abs(max_depth_m - rpt_reported_max_depth_m) < 0.01

    yes_text = "\u662f"
    no_text = "\u5426"
    font = chinese_font()
    plt.rcParams["axes.unicode_minus"] = False
    fig, axes = plt.subplots(3, 1, figsize=(13, 10), sharex=True, constrained_layout=True)

    axes[0].plot(df["time"], df["depth_m"], color="#2563eb", linewidth=2.2, label="OUT\u6c34\u6df1\u66f2\u7ebf\uff1a\u8282\u70b9\u6c34\u6df1")
    axes[0].axhline(rim_depth_m, color="#f97316", linestyle="--", linewidth=2, label=f"\u4e95\u6df1/\u4e95\u76d6\u9ad8\u5ea6 {rim_depth_m:.3f} m")
    axes[0].axhline(rpt_max_depth_m, color="#dc2626", linestyle=":", linewidth=2.2, label=f"RPT\u5185\u90e8\u6700\u5927\u603b\u6c34\u6df1 {rpt_max_depth_m:.3f} m")
    axes[0].axhline(rpt_reported_max_depth_m, color="#16a34a", linestyle="-.", linewidth=1.8, label=f"RPT\u62a5\u544a\u6b65\u957f\u6700\u5927\u6c34\u6df1 {rpt_reported_max_depth_m:.3f} m")
    axes[0].scatter([peak["time"]], [peak["depth_m"]], s=80, color="#dc2626", zorder=5)
    axes[0].annotate(
        f"\u66f2\u7ebf\u5cf0\u503c {peak['depth_m']:.3f} m",
        xy=(peak["time"], peak["depth_m"]),
        xytext=(12, -28),
        textcoords="offset points",
        fontproperties=font,
        arrowprops={"arrowstyle": "->", "color": "#991b1b"},
        color="#991b1b",
    )
    axes[0].set_ylabel("\u8282\u70b9\u603b\u6c34\u6df1 m", fontproperties=font)
    axes[0].set_title("\u8282\u70b9107\u6c34\u6df1\u66f2\u7ebf\u4e0e\u4e95\u76d6\u9ad8\u5ea6/RPT\u6700\u5927\u503c\u5bf9\u7167", fontproperties=font, fontsize=15)
    axes[0].legend(prop=font, loc="upper right")
    axes[0].grid(True, alpha=0.25)

    axes[1].plot(df["time"], df["depth_m"], color="#2563eb", linewidth=2.2, label="OUT\u62a5\u544a\u6b65\u957f\u6c34\u6df1\u653e\u5927\u56fe")
    axes[1].axhline(rpt_reported_max_depth_m, color="#16a34a", linestyle="-.", linewidth=1.8, label=f"RPT\u62a5\u544a\u6b65\u957f\u6700\u5927\u6c34\u6df1 {rpt_reported_max_depth_m:.3f} m")
    axes[1].scatter([peak["time"]], [peak["depth_m"]], s=70, color="#dc2626", zorder=5)
    axes[1].set_ylim(0, max(0.06, max_depth_m * 1.35))
    axes[1].set_ylabel("\u653e\u5927\u6c34\u6df1 m", fontproperties=font)
    axes[1].legend(prop=font, loc="upper right")
    axes[1].grid(True, alpha=0.25)

    axes[2].plot(df["time"], df["ponded_depth_cm"], color="#0f766e", linewidth=2.2, label="\u7531OUT\u6c34\u6df1\u6362\u7b97\u7684\u4e95\u4e0a\u79ef\u6c34\u6df1")
    axes[2].axhline(rpt_max_ponded_depth_cm, color="#dc2626", linestyle=":", linewidth=2.2, label=f"RPT\u5185\u90e8\u6700\u5927\u4e95\u4e0a\u79ef\u6c34 {rpt_max_ponded_depth_cm:.1f} cm")
    axes[2].scatter([pond_peak["time"]], [pond_peak["ponded_depth_cm"]], s=80, color="#dc2626", zorder=5)
    axes[2].annotate(
        f"\u66f2\u7ebf\u5cf0\u503c {pond_peak['ponded_depth_cm']:.1f} cm",
        xy=(pond_peak["time"], pond_peak["ponded_depth_cm"]),
        xytext=(12, -28),
        textcoords="offset points",
        fontproperties=font,
        arrowprops={"arrowstyle": "->", "color": "#991b1b"},
        color="#991b1b",
    )
    axes[2].set_ylabel("\u4e95\u4e0a\u79ef\u6c34\u6df1 cm", fontproperties=font)
    axes[2].set_xlabel("\u65f6\u95f4", fontproperties=font)
    axes[2].legend(prop=font, loc="upper right")
    axes[2].grid(True, alpha=0.25)
    axes[2].xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    for label in axes[2].get_xticklabels():
        label.set_rotation(30)
        label.set_ha("right")

    fig.savefig(PNG_PATH, dpi=180)
    plt.close(fig)

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>\u8282\u70b9107\u6c34\u6df1\u66f2\u7ebf</title>
<style>
body{{font-family:'Microsoft YaHei','SimHei',Arial,sans-serif;margin:28px;background:#f7fafc;color:#172033;}}
.card{{background:white;border-radius:14px;padding:20px;box-shadow:0 8px 24px #12304a18;margin-bottom:18px;}}
img{{max-width:100%;border-radius:10px;border:1px solid #e5e7eb;background:white;}}
table{{border-collapse:collapse;width:100%;}}td,th{{border-bottom:1px solid #e5e7eb;padding:8px;text-align:left;}}th{{background:#eff6ff;}}
</style>
</head>
<body>
<div class="card">
<h1>\u8282\u70b9107\u6c34\u6df1\u66f2\u7ebf\u4e0eRPT\u6700\u5927\u79ef\u6c34\u6df1\u5bf9\u7167</h1>
<table>
<tr><th>\u9879\u76ee</th><th>\u6570\u503c</th></tr>
<tr><td>\u4e95\u6df1/\u4e95\u76d6\u9ad8\u5ea6</td><td>{rim_depth_m:.3f} m</td></tr>
<tr><td>OUT\u66f2\u7ebf\u6700\u5927\u603b\u6c34\u6df1</td><td>{max_depth_m:.3f} m</td></tr>
<tr><td>RPT\u62a5\u544a\u6b65\u957f\u6700\u5927\u6c34\u6df1</td><td>{rpt_reported_max_depth_m:.3f} m</td></tr>
<tr><td>RPT\u5185\u90e8\u6700\u5927\u603b\u6c34\u6df1</td><td>{rpt_max_depth_m:.3f} m\uff0c\u51fa\u73b0\u65f6\u95f4 {rpt_depth_time_of_max}</td></tr>
<tr><td>OUT\u6362\u7b97\u6700\u5927\u4e95\u4e0a\u79ef\u6c34\u6df1</td><td>{max_ponded_cm:.1f} cm</td></tr>
<tr><td>RPT\u5185\u90e8\u6700\u5927\u4e95\u4e0a\u79ef\u6c34\u6df1</td><td>{rpt_max_ponded_depth_cm:.1f} cm\uff0c\u51fa\u73b0\u65f6\u95f4 {rpt_flood_time_of_max}</td></tr>
<tr><td>OUT\u66f2\u7ebf\u662f\u5426\u8fbe\u5230RPT\u5185\u90e8\u6700\u5927\u4e95\u4e0a\u79ef\u6c34\u6df1</td><td>{yes_text if reaches_internal_max else no_text}</td></tr>
<tr><td>OUT\u66f2\u7ebf\u662f\u5426\u63a5\u8fd1RPT\u62a5\u544a\u6b65\u957f\u6700\u5927\u6c34\u6df1</td><td>{yes_text if reaches_reported_max else no_text}</td></tr>
</table>
<p>\u8ba1\u7b97\u5173\u7cfb\uff1a\u4e95\u4e0a\u79ef\u6c34\u6df1 = max(0, OUT\u8282\u70b9\u603b\u6c34\u6df1 - INP\u4e95\u6df1)\u3002\u8282\u70b9107\u7684RPT\u5185\u90e8\u6700\u5927\u503c\u51fa\u73b0\u57280 00:00\uff0c\u800cOUT\u62a5\u544a\u65f6\u95f4\u5e8f\u5217\u4ece00:10\u5f00\u59cb\uff0c\u56e0\u6b64OUT\u66f2\u7ebf\u6ca1\u6709\u8fbe\u5230RPT\u5185\u90e8\u6700\u5927\u4e95\u4e0a\u79ef\u6c34\u6df1\uff1bOUT\u66f2\u7ebf\u53ea\u5bf9\u5e94\u62a5\u544a\u6b65\u957f\u4fdd\u5b58\u4e0b\u6765\u7684\u6c34\u6df1\u3002</p>
</div>
<div class="card"><img src="{PNG_PATH.name}" alt="\u8282\u70b9107\u6c34\u6df1\u66f2\u7ebf"></div>
</body>
</html>"""
    HTML_PATH.write_text(html, encoding="utf-8")

    print(f"png={PNG_PATH}")
    print(f"html={HTML_PATH}")
    print(f"csv={CSV_PATH}")
    print(f"rim_depth_m={rim_depth_m:.6f}")
    print(f"out_max_depth_m={max_depth_m:.6f}")
    print(f"rpt_reported_max_depth_m={rpt_reported_max_depth_m:.6f}")
    print(f"rpt_internal_max_depth_m={rpt_max_depth_m:.6f}")
    print(f"out_max_ponded_depth_cm={max_ponded_cm:.6f}")
    print(f"rpt_max_ponded_depth_cm={rpt_max_ponded_depth_cm:.6f}")
    print(f"diff_cm={max_ponded_cm - rpt_max_ponded_depth_cm:.6f}")
    print(f"reaches_internal_max={reaches_internal_max}")
    print(f"reaches_reported_max={reaches_reported_max}")


if __name__ == "__main__":
    main()
