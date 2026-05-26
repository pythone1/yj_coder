"""
项目名称: forklift-monitoring-yolo-uwb
技术领域: 02-computer-vision
模块说明: uwb_report.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

from __future__ import annotations

from html import escape
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from forklift_monitoring.core.config import SiteConfig
from forklift_monitoring.uwb.pipeline import UWBPipelineResult


def generate_uwb_report(
    site_config: SiteConfig,
    result: UWBPipelineResult,
    output_dir: str | Path,
    title: str = "UWB Path Counting Report",
) -> dict[str, str]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    image_path = output_dir / "uwb_report.png"
    html_path = output_dir / "uwb_report.html"

    _draw_trajectory_chart(site_config, result, image_path, title)
    _write_html_report(site_config, result, image_path.name, html_path, title)

    return {"image": str(image_path), "html": str(html_path)}


def _draw_trajectory_chart(site_config: SiteConfig, result: UWBPipelineResult, image_path: Path, title: str) -> None:
    fig, ax = plt.subplots(figsize=(10, 8))

    zone_colors = {"A": "#F6BD60", "B": "#84A59D", "C": "#F28482"}
    for zone_name, zone in site_config.zones.items():
        xs = [p[0] for p in zone.polygon] + [zone.polygon[0][0]]
        ys = [p[1] for p in zone.polygon] + [zone.polygon[0][1]]
        ax.fill(xs, ys, alpha=0.25, color=zone_colors.get(zone_name, "#CCCCCC"))
        ax.plot(xs, ys, color=zone_colors.get(zone_name, "#666666"), linewidth=2)
        center_x = sum(p[0] for p in zone.polygon) / len(zone.polygon)
        center_y = sum(p[1] for p in zone.polygon) / len(zone.polygon)
        ax.text(center_x, center_y, zone_name, fontsize=16, weight="bold", ha="center", va="center")

    if result.frames:
        xs = [frame.x for frame in result.frames]
        ys = [frame.y for frame in result.frames]
        ax.plot(xs, ys, color="#355070", linewidth=2.5, marker="o", markersize=4, label="UWB Track")

        start = result.frames[0]
        end = result.frames[-1]
        ax.scatter([start.x], [start.y], color="#2A9D8F", s=120, label="Start", zorder=5)
        ax.scatter([end.x], [end.y], color="#E63946", s=120, label="End", zorder=5)

    for event in result.events:
        matched = None
        for frame in result.frames:
            if frame.timestamp_ms == event.timestamp_ms and frame.tag_id == event.tag_id:
                matched = frame
                break
        if matched is not None:
            ax.scatter([matched.x], [matched.y], color="#D00000", s=150, marker="*", zorder=6)
            ax.text(matched.x, matched.y + 0.35, event.path_name, fontsize=10, ha="center")

    ax.set_title(title, fontsize=16)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper right")
    ax.set_aspect("equal", adjustable="box")
    fig.tight_layout()
    fig.savefig(image_path, dpi=150)
    plt.close(fig)


def _write_html_report(
    site_config: SiteConfig,
    result: UWBPipelineResult,
    image_name: str,
    html_path: Path,
    title: str,
) -> None:
    counts_items = "".join(
        f"<li><strong>{escape(key)}</strong>: {value}</li>"
        for key, value in sorted(result.counts.items())
    ) or "<li>暂无计数结果</li>"

    event_rows = "".join(
        f"<tr><td>{event.timestamp_ms}</td><td>{escape(event.tag_id)}</td><td>{escape(event.path_name)}</td>"
        f"<td>{escape(event.origin)}</td><td>{escape(event.destination)}</td></tr>"
        for event in result.events
    ) or "<tr><td colspan='5'>暂无事件</td></tr>"

    step_rows = "".join(
        [
            "<tr><td>1</td><td>读取 UWB 坐标流</td><td>拿到每个时间点的 tag_id、x、y</td></tr>",
            "<tr><td>2</td><td>轨迹平滑</td><td>消除短时抖动，避免区域切换误判</td></tr>",
            "<tr><td>3</td><td>区域判定</td><td>判断当前点落在 A、B、C 哪个区域</td></tr>",
            "<tr><td>4</td><td>状态机计数</td><td>只有完成 A→C 或 B→C 才记 1 次</td></tr>",
            "<tr><td>5</td><td>输出结果</td><td>生成计数、事件表和轨迹图</td></tr>",
        ]
    )

    zone_rows = "".join(
        f"<tr><td>{escape(name)}</td><td>{escape(str(zone.polygon))}</td></tr>"
        for name, zone in site_config.zones.items()
    )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>{escape(title)}</title>
  <style>
    body {{ font-family: 'Microsoft YaHei', sans-serif; margin: 24px; color: #222; background: #f7f7f7; }}
    h1, h2 {{ margin-bottom: 8px; }}
    .card {{ background: white; border-radius: 12px; padding: 18px 20px; margin-bottom: 18px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
    th, td {{ border: 1px solid #ddd; padding: 8px 10px; text-align: left; }}
    th {{ background: #f0f0f0; }}
    img {{ max-width: 100%; border-radius: 8px; border: 1px solid #ddd; background: white; }}
    .muted {{ color: #666; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>{escape(title)}</h1>
    <div class="muted">这份页面用来回答三个问题：车走了哪条路、为什么这样计数、每一步系统在做什么。</div>
  </div>

  <div class="card">
    <h2>1. 最终计数</h2>
    <ul>{counts_items}</ul>
  </div>

  <div class="card">
    <h2>2. 轨迹可视化</h2>
    <img src="{escape(image_name)}" alt="uwb trajectory report" />
  </div>

  <div class="card">
    <h2>3. 每一步在做什么</h2>
    <table>
      <thead><tr><th>步骤</th><th>处理动作</th><th>作用</th></tr></thead>
      <tbody>{step_rows}</tbody>
    </table>
  </div>

  <div class="card">
    <h2>4. 事件明细</h2>
    <table>
      <thead><tr><th>时间戳</th><th>车辆/标签</th><th>路径</th><th>起点</th><th>终点</th></tr></thead>
      <tbody>{event_rows}</tbody>
    </table>
  </div>

  <div class="card">
    <h2>5. 区域配置</h2>
    <table>
      <thead><tr><th>区域</th><th>多边形坐标</th></tr></thead>
      <tbody>{zone_rows}</tbody>
    </table>
  </div>
</body>
</html>
"""
    html_path.write_text(html, encoding="utf-8")
