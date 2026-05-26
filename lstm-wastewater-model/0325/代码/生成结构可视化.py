from __future__ import annotations

import json
import heapq
from collections import defaultdict
from dataclasses import replace
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from 公共配置与数据 import (
    实验配置,
    基线模型路径,
    结果目录,
    读取_inp分段,
    提取数据行,
    读取坐标,
    读取连边,
)


def 计算主干路径(outfall: str = "J132") -> list[str]:
    """按无向最短路径树找出距离排口最远的一条主干长路径。"""
    edges = 读取连边(基线模型路径)
    adj: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for _, a, b, length in edges:
        adj[a].append((b, length))
        adj[b].append((a, length))

    dist = {outfall: 0.0}
    prev: dict[str, str] = {}
    heap = [(0.0, outfall)]
    while heap:
        current_dist, node = heapq.heappop(heap)
        if current_dist != dist[node]:
            continue
        for nb, length in adj[node]:
            nd = current_dist + length
            if nd < dist.get(nb, 1e18):
                dist[nb] = nd
                prev[nb] = node
                heapq.heappush(heap, (nd, nb))

    target = max(dist.items(), key=lambda kv: kv[1])[0]
    path = [target]
    while path[-1] != outfall:
        path.append(prev[path[-1]])
    return path


def 生成全网结构图(config: 实验配置) -> Path:
    coords = 读取坐标(基线模型路径)
    edges = 读取连边(基线模型路径)
    trunk_path = 计算主干路径(config.唯一排口)
    trunk_set = set(trunk_path)
    candidate_set = set(config.候选节点)
    monitor_set = set(config.监测点)
    truth_set = set(config.真值注入点)

    fig = go.Figure()

    # 全网灰色连边
    edge_x: list[float] = []
    edge_y: list[float] = []
    for _, a, b, _ in edges:
        if a not in coords or b not in coords:
            continue
        edge_x.extend([coords[a][0], coords[b][0], None])
        edge_y.extend([coords[a][1], coords[b][1], None])
    fig.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line=dict(color="#cbd5e1", width=1),
            hoverinfo="skip",
            name="全网连边",
        )
    )

    # 主干高亮
    trunk_x: list[float] = []
    trunk_y: list[float] = []
    for a, b in zip(trunk_path[:-1], trunk_path[1:]):
        if a in coords and b in coords:
            trunk_x.extend([coords[a][0], coords[b][0], None])
            trunk_y.extend([coords[a][1], coords[b][1], None])
    fig.add_trace(
        go.Scatter(
            x=trunk_x,
            y=trunk_y,
            mode="lines",
            line=dict(color="#f59e0b", width=4),
            hoverinfo="skip",
            name="排口主干长路径",
        )
    )

    # 全网节点
    all_nodes = list(coords.keys())
    fig.add_trace(
        go.Scatter(
            x=[coords[n][0] for n in all_nodes],
            y=[coords[n][1] for n in all_nodes],
            mode="markers",
            marker=dict(size=4, color="#94a3b8"),
            text=all_nodes,
            hovertemplate="节点=%{text}<extra></extra>",
            name="全网节点",
        )
    )

    def add_nodes(nodes: list[str], name: str, color: str, symbol: str, size: int) -> None:
        fig.add_trace(
            go.Scatter(
                x=[coords[n][0] for n in nodes if n in coords],
                y=[coords[n][1] for n in nodes if n in coords],
                mode="markers+text",
                marker=dict(size=size, color=color, symbol=symbol, line=dict(width=1, color="#0f172a")),
                text=nodes,
                textposition="top center",
                hovertemplate="节点=%{text}<extra></extra>",
                name=name,
            )
        )

    add_nodes(list(candidate_set), "20个候选节点", "#2563eb", "circle", 10)
    add_nodes(list(monitor_set), "5个监测点", "#16a34a", "square", 12)
    add_nodes(list(truth_set), "3个真值注入点", "#dc2626", "star", 15)
    add_nodes([config.唯一排口], "唯一排口", "#7c3aed", "diamond", 16)

    summary_html = f"""
    <div style="font-family:'Microsoft YaHei',sans-serif;line-height:1.8">
      <h2>0325 全网结构与主干选点</h2>
      <p>本图直接基于处理后的原始 dry INP 生成。灰色为全网节点与连边，橙色为通向唯一排口 J132 的主干长路径。</p>
      <p>当前 20 个候选节点按主干长路径等间距抽样；3 个真值注入点和 5 个监测点都从这条主干上选取。</p>
      <p><b>唯一排口：</b>{config.唯一排口}</p>
      <p><b>20 个候选节点：</b>{'、'.join(config.候选节点)}</p>
      <p><b>3 个真值注入点：</b>{'、'.join(config.真值注入点)}</p>
      <p><b>5 个监测点：</b>{'、'.join(config.监测点)}</p>
    </div>
    """

    fig.update_layout(
        title="0325 原始全网与主干 20 节点选点方案",
        template="plotly_white",
        width=1500,
        height=900,
        margin=dict(l=30, r=30, t=80, b=30),
        xaxis=dict(title="X 坐标"),
        yaxis=dict(title="Y 坐标", scaleanchor="x", scaleratio=1),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0.01),
        annotations=[
            dict(
                text=summary_html,
                xref="paper",
                yref="paper",
                x=0.01,
                y=0.99,
                showarrow=False,
                align="left",
                bgcolor="rgba(255,255,255,0.92)",
                bordercolor="#cbd5e1",
                borderwidth=1,
                xanchor="left",
                yanchor="top",
            )
        ],
    )

    output = 结果目录 / "0325_原始全网选点方案.html"
    pio.write_html(fig, file=str(output), include_plotlyjs="cdn", full_html=True)

    # 同步保存一份 JSON 方案，方便后续核对。
    (结果目录 / "0325_方案.json").write_text(
        json.dumps(
            {
                "唯一排口": config.唯一排口,
                "主干长路径": trunk_path,
                "候选节点": list(config.候选节点),
                "真值注入点": list(config.真值注入点),
                "监测点": list(config.监测点),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return output


def 生成监测拟合图(
    observed_delta: pd.DataFrame,
    sim_delta: pd.DataFrame,
    config: 实验配置,
) -> Path:
    fig = go.Figure()
    for node_name in config.监测点:
        fig.add_trace(
            go.Scatter(
                x=observed_delta["步号"],
                y=observed_delta[node_name],
                mode="lines",
                name=f"{node_name} 观测增量",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=sim_delta["步号"],
                y=sim_delta[node_name],
                mode="lines",
                line=dict(dash="dash"),
                name=f"{node_name} 模拟增量",
            )
        )
    fig.update_layout(
        title="0325 监测点流量增量拟合",
        template="plotly_white",
        xaxis_title="10分钟步号",
        yaxis_title="流量增量 (CMS)",
        width=1400,
        height=800,
    )
    output = 结果目录 / "0325_监测拟合.html"
    pio.write_html(fig, file=str(output), include_plotlyjs="cdn", full_html=True)
    return output


def 生成指定方案结构图(
    config: 实验配置,
    output_name: str,
    title: str,
    summary_title: str,
    extra_lines: list[str] | None = None,
) -> Path:
    """按指定配置生成全网结构图。

    这个函数用于在不改主实验配置的前提下，先把备选的注入点/监测点方案画出来给用户确认。
    """

    coords = 读取坐标(基线模型路径)
    edges = 读取连边(基线模型路径)
    trunk_path = 计算主干路径(config.唯一排口)
    candidate_set = set(config.候选节点)
    monitor_set = set(config.监测点)
    truth_set = set(config.真值注入点)

    fig = go.Figure()

    edge_x: list[float] = []
    edge_y: list[float] = []
    for _, a, b, _ in edges:
        if a not in coords or b not in coords:
            continue
        edge_x.extend([coords[a][0], coords[b][0], None])
        edge_y.extend([coords[a][1], coords[b][1], None])
    fig.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line=dict(color="#cbd5e1", width=1),
            hoverinfo="skip",
            name="全网连边",
        )
    )

    trunk_x: list[float] = []
    trunk_y: list[float] = []
    for a, b in zip(trunk_path[:-1], trunk_path[1:]):
        if a in coords and b in coords:
            trunk_x.extend([coords[a][0], coords[b][0], None])
            trunk_y.extend([coords[a][1], coords[b][1], None])
    fig.add_trace(
        go.Scatter(
            x=trunk_x,
            y=trunk_y,
            mode="lines",
            line=dict(color="#f59e0b", width=4),
            hoverinfo="skip",
            name="排口主干长路径",
        )
    )

    all_nodes = list(coords.keys())
    fig.add_trace(
        go.Scatter(
            x=[coords[n][0] for n in all_nodes],
            y=[coords[n][1] for n in all_nodes],
            mode="markers",
            marker=dict(size=4, color="#94a3b8"),
            text=all_nodes,
            hovertemplate="节点=%{text}<extra></extra>",
            name="全网节点",
        )
    )

    def add_nodes(nodes: list[str], name: str, color: str, symbol: str, size: int) -> None:
        valid = [n for n in nodes if n in coords]
        fig.add_trace(
            go.Scatter(
                x=[coords[n][0] for n in valid],
                y=[coords[n][1] for n in valid],
                mode="markers+text",
                marker=dict(size=size, color=color, symbol=symbol, line=dict(width=1, color="#0f172a")),
                text=valid,
                textposition="top center",
                hovertemplate="节点=%{text}<extra></extra>",
                name=name,
            )
        )

    add_nodes(list(candidate_set), "20个候选节点", "#2563eb", "circle", 10)
    add_nodes(list(monitor_set), "监测点方案", "#16a34a", "square", 12)
    add_nodes(list(truth_set), "3个注入点", "#dc2626", "star", 15)
    add_nodes([config.唯一排口], "唯一排口", "#7c3aed", "diamond", 16)

    extra = "".join(f"<p>{line}</p>" for line in (extra_lines or []))
    summary_html = f"""
    <div style="font-family:'Microsoft YaHei',sans-serif;line-height:1.8">
      <h2>{summary_title}</h2>
      <p>灰色为全网节点与连边，橙色为通向唯一排口 J132 的主干长路径。</p>
      <p>蓝色为 20 个候选节点，红色为 3 个注入点，绿色为当前建议监测点，紫色为唯一排口。</p>
      <p><b>唯一排口：</b>{config.唯一排口}</p>
      <p><b>20 个候选节点：</b>{'、'.join(config.候选节点)}</p>
      <p><b>3 个注入点：</b>{'、'.join(config.真值注入点)}</p>
      <p><b>建议监测点：</b>{'、'.join(config.监测点)}</p>
      {extra}
    </div>
    """

    fig.update_layout(
        title=title,
        template="plotly_white",
        width=1500,
        height=900,
        margin=dict(l=30, r=30, t=80, b=30),
        xaxis=dict(title="X 坐标"),
        yaxis=dict(title="Y 坐标", scaleanchor="x", scaleratio=1),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0.01),
        annotations=[
            dict(
                text=summary_html,
                xref="paper",
                yref="paper",
                x=0.01,
                y=0.99,
                showarrow=False,
                align="left",
                bgcolor="rgba(255,255,255,0.92)",
                bordercolor="#cbd5e1",
                borderwidth=1,
                xanchor="left",
                yanchor="top",
            )
        ],
    )

    output = 结果目录 / output_name
    pio.write_html(fig, file=str(output), include_plotlyjs="cdn", full_html=True)
    return output


def 生成监测点重构建议图() -> Path:
    """生成“监测点必须包住所有注入点”的建议方案图。"""

    base = 实验配置()
    proposal = replace(
        base,
        真值注入点=("J89", "J225", "J140"),
        监测点=("J78", "J59", "J226", "J135", "J231"),
    )
    extra_lines = [
        "建议逻辑：去掉 J172 这类上游支向争议点，只保留更靠中下游主干的 3 个注入点。",
        "J89 位于 J78 与 J59 之间；J225 位于 J226 与 J135 之间；J140 位于 J135 与 J231 之间。",
        "监测点按“前后包住注入点”的思路摆放，避免只在单侧末端观察变化。",
        "该图仅用于确认监测点空间布局，暂未写回主实验配置。",
    ]
    return 生成指定方案结构图(
        proposal,
        output_name="0325_监测点重构建议.html",
        title="0325 监测点重构建议（先确认布局，再回写主实验）",
        summary_title="0325 监测点重构建议",
        extra_lines=extra_lines,
    )


def 生成主干连续20点建议图() -> Path:
    """生成基于整段连通主干走廊的重构建议图。

    这版不再沿用之前错误的“无向长路径等间距抽样”结果，
    而是直接在用户更认可的中下游主干连续区段上布设 20 个候选点，
    注入点与监测点都在这条连续主干上布置。
    """

    proposal = 实验配置(
        候选节点=(
            "J89",
            "J91",
            "J237",
            "J59",
            "J120",
            "J240",
            "J124",
            "J125",
            "J226",
            "J129",
            "J225",
            "J133",
            "J135",
            "J137",
            "J140",
            "J142",
            "J230",
            "J145",
            "J231",
            "J132",
        ),
        真值注入点=("J89", "J225", "J140"),
        监测点=("J91", "J59", "J226", "J135", "J231"),
    )
    extra_lines = [
        "这版把候选节点压缩到 J89 → J132 的连续主干走廊上，避免把明显枝干点混进来。",
        "3 个注入点全部放在这条连续主干上：J89、J225、J140。",
        "5 个监测点按包络思路布设：J91 包住上游注入段，J59/J226/J135 依次分隔中段，J231 控制末端到排口的响应。",
        "如果你确认这版结构，再正式回写主实验配置并重跑。",
    ]
    return 生成指定方案结构图(
        proposal,
        output_name="0325_主干连续20点建议.html",
        title="0325 连续主干 20 点重构建议（先确认结构，再回写配置）",
        summary_title="0325 连续主干 20 点建议",
        extra_lines=extra_lines,
    )


def 生成全局分散20点建议图() -> Path:
    """生成沿整段主干全局分散布点的建议图。"""

    proposal = 实验配置(
        候选节点=(
            "J19",
            "J172",
            "J168",
            "J191",
            "J71",
            "J78",
            "J85",
            "J89",
            "J237",
            "J59",
            "J240",
            "J125",
            "J226",
            "J129",
            "J225",
            "J135",
            "J140",
            "J145",
            "J231",
            "J132",
        ),
        真值注入点=("J191", "J89", "J140"),
        监测点=("J168", "J78", "J59", "J129", "J231"),
    )
    extra_lines = [
        "这版按整段主干做全局分散布点，不再把候选点和注入点集中在后段。",
        "3 个注入点分别位于主干上游、中游、下游：J191、J89、J140。",
        "5 个监测点用于包络这三个注入区段：J168/J78 包住上游，J78/J59 包住中游，J129/J231 包住下游。",
        "如果你认可这版全局结构，再正式回写主实验配置并重跑。",
    ]
    return 生成指定方案结构图(
        proposal,
        output_name="0325_全局分散20点建议.html",
        title="0325 全局分散主干 20 点建议（先确认结构，再回写配置）",
        summary_title="0325 全局分散主干 20 点建议",
        extra_lines=extra_lines,
    )


def 生成结构审计后全局建议图() -> Path:
    """按“主干候选点 + 汇入监测点”的思路生成更稳的一版全局建议图。"""

    proposal = 实验配置(
        候选节点=(
            "J176",
            "J172",
            "J168",
            "J191",
            "J71",
            "J78",
            "J85",
            "J89",
            "J91",
            "J59",
            "J240",
            "J125",
            "J226",
            "J129",
            "J225",
            "J135",
            "J140",
            "J145",
            "J67",
            "J231",
        ),
        真值注入点=("J191", "J89", "J140"),
        监测点=("J166", "J237", "J226", "J145", "J231"),
    )
    extra_lines = [
        "候选点选择原则：尽量用连续走廊上的度为 2 的主干节点，少用分叉/枝干节点。",
        "监测点选择原则：优先放在关键汇入节点或其附近控制位，用来前后包络 3 个注入区段。",
        "3 个注入点分散在上游、中游、下游：J191、J89、J140。",
        "5 个监测点按包络关系布置：J166 包住上游段，J237 控制中上游汇入，J226 控制中下游，J145/J231 控制近排口段。",
    ]
    return 生成指定方案结构图(
        proposal,
        output_name="0325_结构审计后全局建议.html",
        title="0325 结构审计后全局选点建议（先确认，再回写主实验）",
        summary_title="0325 结构审计后全局选点建议",
        extra_lines=extra_lines,
    )


def 生成深度审计后走廊建议图() -> Path:
    """生成基于 J191→J132 连续走廊的重构建议图。"""

    proposal = 实验配置(
        候选节点=(
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
        ),
        真值注入点=("J76", "J124", "J140"),
        监测点=("J191", "J91", "J59", "J126", "J231"),
    )
    extra_lines = [
        "这版直接以 J191 → J132 的连续主干走廊为研究区，不再把更上游的 J176/J172 一带混进来。",
        "20 个候选点全部放在这条连续走廊上，尽量避开 J237/J238 这类分叉控制点本身。",
        "3 个注入点按上中下游分散：J76、J124、J140。",
        "5 个监测点用于包络整段候选区间：J191 为上边界，J91/J59/J126 为中间控制点，J231 为下边界。",
    ]
    return 生成指定方案结构图(
        proposal,
        output_name="0325_深度审计后走廊建议.html",
        title="0325 深度审计后连续走廊建议（先确认，再回写主实验）",
        summary_title="0325 深度审计后连续走廊建议",
        extra_lines=extra_lines,
    )


def 生成加密监测布设建议图() -> Path:
    """在当前 20 个候选点与 3 个注入点不变的前提下，给出一版更密的监测点布设建议。

    设计原则：
    1. 注入点附近必须有前后监测；
    2. 关键控制节点仍要保留；
    3. 整段候选走廊必须被上游/下游边界监测包住。
    """

    base = 实验配置()
    proposal = replace(
        base,
        监测点=(
            "J191",  # 上边界，包住最上游候选段
            "J74",   # J76 上游近邻
            "J78",   # J76 下游近邻
            "J91",   # 上中游关键控制位
            "J59",   # 中游关键控制位
            "J123",  # J124 上游近邻
            "J126",  # J124 下游关键控制位
            "J137",  # J140 上游近邻
            "J145",  # J140 下游近邻
            "J231",  # 下边界，包住最下游候选段
        ),
    )
    extra_lines = [
        "这版不改 20 个候选点，也不改 3 个注入点，只增加监测点密度。",
        "J76 由 J74/J78 前后包住；J124 由 J123/J126 前后包住；J140 由 J137/J145 前后包住。",
        "J91、J59、J126 同时承担关键控制节点角色；J191 与 J231 作为整段候选走廊的上下边界监测点。",
        "如果你认可这版布局，下一步再把主实验监测点正式切换到这套加密方案。",
    ]
    return 生成指定方案结构图(
        proposal,
        output_name="0325_加密监测布设建议.html",
        title="0325 加密监测布设建议（先确认，再回写主实验）",
        summary_title="0325 加密监测布设建议",
        extra_lines=extra_lines,
    )
