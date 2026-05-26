from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd


项目根目录 = Path(r"E:\PY\LSTM\0325")
代码目录 = 项目根目录 / "代码"
数据目录 = 项目根目录 / "数据"
结果目录 = 项目根目录 / "结果"
运行时数据目录 = 项目根目录 / "runtime_data"

# 供 PySWMM 使用的 ASCII 路径副本，避免中文目录名导致读取失败。
基线模型路径 = 运行时数据目录 / "base_model_0325.inp"


@dataclass(frozen=True)
class 实验配置:
    """0325 当前主实验配置。

    当前版本遵循用户最新要求：
    1. 唯一排口固定为 J132；
    2. 20 个候选节点沿通向排口的主干长路径分散选取；
    3. 监测点也从同一主干中选取；
    4. 总入流量 Q_R 直接取三处真值注入总量积分；
    5. 事件时长 8 小时，分析分辨率 10 分钟；
    6. 先用小参数 GA/AM 跑通整条链路。
    """

    时间步秒数: int = 600
    事件时长小时: int = 8
    唯一排口: str = "J132"
    雨量时序名: str = "2天污水量"

    # 20 个候选节点现在按用户确认后的“连续主干走廊”方案固定。
    # 这批点从 J191 → J132 这一连续主干区间中抽取，尽量避开明显枝干点与汇入控制点本身。
    候选节点: Tuple[str, ...] = (
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
    )

    # 三个真值注入点按用户确认后的上/中/下游分散方案固定。
    # 三个点共享同一条 8 小时总入流波形，只是在总量上不同。
    真值注入点: Tuple[str, ...] = ("J76", "J124", "J140")

    # 监测点采用加密布设方案：
    # 1. J191 / J231 作为整段候选走廊的上下边界；
    # 2. J74 / J78 前后夹住 J76；
    # 3. J123 / J126 前后夹住 J124；
    # 4. J137 / J145 前后夹住 J140；
    # 5. J91 / J59 / J126 同时承担关键控制节点角色。
    监测点: Tuple[str, ...] = ("J191", "J74", "J78", "J91", "J59", "J123", "J126", "J137", "J145", "J231")

    # 三个注入点总量不同，用来构造强度不同的受控事件。
    真值总体积立方米: Tuple[float, ...] = (18000.0, 26000.0, 32000.0)

    # 当前改成更强一档的 GA：
    # 目标是在不改模型、不改选点的前提下，提高全局搜索覆盖度与初始 PPD 多样性。
    ga_种群数: int = 5
    ga_单群规模: int = 24
    ga_迭代代数: int = 18
    ga_精英比例: float = 0.20
    ga_变异强度: float = 0.20
    ga_迁移间隔代数: int = 5
    ga_迁移个体数: int = 2
    ga_跨代topk保留数: int = 80
    initial_ppd保留比例: float = 0.40
    # initial PPD 不再按固定套数硬截断，而是根据高分区间自适应保留。
    initial_ppd最小保留数: int = 24
    initial_ppd最大保留数: int = 64
    initial_ppd相对最优容差: float = 0.08
    initial_ppd分位数阈值: float = 0.75
    initial_ppd权重温度: float = 0.03

    am_链数: int = 4
    am_每链样本: int = 240
    am_预热: int = 60
    am_自适应起点: int = 30
    am_基础协方差: float = 0.002
    am_协方差微扰: float = 1e-6
    # posterior 修正：
    # 1. 似然项按观测方差做标准化，避免量纲不一致导致过弱；
    # 2. 先验强度单独缩放，避免 prior 压过 likelihood；
    # 3. prior 改成 initial PPD 样本混合核，而不是单高斯。
    am_似然方差倍数: float = 4.0
    am_先验强度: float = 0.35
    am_先验核协方差放大倍数: float = 1.50
    posterior_validation_sample_count: int = 12
    并行工作进程数: int = 6

    @property
    def 事件步数(self) -> int:
        return int(self.事件时长小时 * 3600 / self.时间步秒数)


def 读取_inp分段(inp_path: Path) -> Dict[str, List[str]]:
    text = inp_path.read_text(encoding="utf-8", errors="ignore")
    sections: Dict[str, List[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            current = stripped[1:-1]
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    return sections


def 提取数据行(sections: Dict[str, List[str]], section_name: str) -> List[List[str]]:
    rows: List[List[str]] = []
    for line in sections.get(section_name, []):
        stripped = line.strip()
        if not stripped or stripped.startswith(";"):
            continue
        rows.append(stripped.split())
    return rows


def 读取坐标(inp_path: Path | None = None) -> Dict[str, Tuple[float, float]]:
    path = inp_path or 基线模型路径
    sections = 读取_inp分段(path)
    return {
        row[0]: (float(row[1]), float(row[2]))
        for row in 提取数据行(sections, "COORDINATES")
        if len(row) >= 3
    }


def 读取连边(inp_path: Path | None = None) -> List[Tuple[str, str, str, float]]:
    path = inp_path or 基线模型路径
    sections = 读取_inp分段(path)
    edges: List[Tuple[str, str, str, float]] = []
    for row in 提取数据行(sections, "CONDUITS"):
        if len(row) >= 4:
            edges.append((row[0], row[1], row[2], float(row[3])))
    for row in 提取数据行(sections, "PUMPS"):
        if len(row) >= 3:
            # 泵没有长度，给一个小的等效长度用于可视化/最短路径近似。
            edges.append((row[0], row[1], row[2], 50.0))
    return edges


def 读取时序(inp_path: Path | None = None, series_name: str = "2天污水量") -> pd.DataFrame:
    """从 INP 的 TIMESERIES 段读取指定时序。

    当前用于提取原始模型中的降雨强度曲线。返回的步号统一视为等步长序列，
    后续再按照当前实验的 10 分钟时间轴做重采样/裁切。
    """

    path = inp_path or 基线模型路径
    sections = 读取_inp分段(path)
    rows = []
    for row in 提取数据行(sections, "TIMESERIES"):
        if len(row) >= 3 and row[0] == series_name:
            rows.append(
                {
                    "序列名": row[0],
                    "步号": int(float(row[1])),
                    "值": float(row[2]),
                }
            )
    if not rows:
        raise ValueError(f"未在 INP 的 TIMESERIES 段找到时序 {series_name}")
    df = pd.DataFrame(rows).sort_values("步号").reset_index(drop=True)
    return df


def 获取工作模型路径(worker_tag: str | None = None) -> Path:
    """为并行 SWMM 进程分配独立的 INP 副本路径。"""

    tag = worker_tag or f"worker_{os.getpid()}"
    worker_dir = 运行时数据目录 / "workers" / tag
    worker_dir.mkdir(parents=True, exist_ok=True)
    target = worker_dir / "base_model_0325.inp"
    if (not target.exists()) or 基线模型路径.stat().st_mtime > target.stat().st_mtime:
        target.write_text(基线模型路径.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
    return target


def 构造总入流时间权重(config: 实验配置) -> pd.DataFrame:
    """构造 8 小时总入流波形。

    这里严格区分两层：
    1. 先用原始 INP 中真实存在的 `2天污水量` 时序，生成一条 8 小时总入流波形；
    2. 再把这条“总入流波形”按节点份额拆分到各真值注入点。

    这一步得到的是区域总入流在 48 个 10 分钟时段上的分配比例，而不是单个节点的入流。
    """

    raw = 读取时序(基线模型路径, config.雨量时序名)
    values = raw["值"].to_numpy(dtype=float)
    if len(values) != config.事件步数:
        old_x = np.linspace(0.0, 1.0, len(values))
        new_x = np.linspace(0.0, 1.0, config.事件步数)
        values = np.interp(new_x, old_x, values)

    smooth = pd.Series(values).rolling(window=3, center=True, min_periods=1).mean().to_numpy(dtype=float)
    optimized = 0.35 * values + 0.65 * smooth
    optimized = np.maximum(optimized, 1e-9)
    权重 = optimized / optimized.sum()
    小时序列 = np.arange(config.事件步数) * config.时间步秒数 / 3600.0
    return pd.DataFrame(
        {
            "步号": np.arange(config.事件步数),
            "相对小时": 小时序列,
            "原始降雨强度": values,
            "平滑后强度": smooth,
            "总入流相对波形": optimized,
            "时间权重": 权重,
        }
    )


def 构造总入流过程(config: 实验配置) -> pd.DataFrame:
    """把总入流量 Q_R 按时间权重拆成 48 个 10 分钟时段的总入流过程。"""

    weights_df = 构造总入流时间权重(config)
    total_qr = float(sum(config.真值总体积立方米))
    rows: List[dict] = []
    for _, row in weights_df.iterrows():
        step_volume = float(total_qr * row["时间权重"])
        rows.append(
            {
                "步号": int(row["步号"]),
                "相对小时": float(row["相对小时"]),
                "时间权重": float(row["时间权重"]),
                "总入流体积_m3": step_volume,
                "总入流量_CMS": step_volume / config.时间步秒数,
            }
        )
    return pd.DataFrame(rows)


def 构造真值注水(config: 实验配置) -> pd.DataFrame:
    """把总入流波形按三处真值点份额拆分成逐时注入序列。

    逻辑是：
    1. 先构造 8 小时总入流过程；
    2. 三个真值点共用这条总波形；
    3. 再按各自总量占比，把总入流拆分到各节点；
    4. 得到每个节点每个 10 分钟时段的注入体积与流量。
    """

    total_df = 构造总入流过程(config)
    total_qr = float(sum(config.真值总体积立方米))
    rows: List[dict] = []
    for 节点, 总体积 in zip(config.真值注入点, config.真值总体积立方米):
        share = 总体积 / total_qr
        for _, row in total_df.iterrows():
            步体积 = float(row["总入流体积_m3"] * share)
            rows.append(
                {
                    "节点": 节点,
                    "步号": int(row["步号"]),
                    "相对小时": float(row["相对小时"]),
                    "时间权重": float(row["时间权重"]),
                    "节点总量占比": float(share),
                    "该步体积_m3": 步体积,
                    "注入流量_CMS": 步体积 / config.时间步秒数,
                }
            )
    return pd.DataFrame(rows)


def 根据总体积生成节点注入序列(
    节点总体积映射: Dict[str, float],
    config: 实验配置,
) -> Dict[str, np.ndarray]:
    total_qr = float(sum(节点总体积映射.values()))
    if total_qr <= 0:
        return {}
    total_df = 构造总入流过程(config)
    total_step_volume = total_df["总入流体积_m3"].to_numpy(dtype=float)
    return {
        节点: (总体积 / total_qr) * total_step_volume / config.时间步秒数
        for 节点, 总体积 in 节点总体积映射.items()
    }


def 保存基础数据(config: 实验配置) -> None:
    结果目录.mkdir(parents=True, exist_ok=True)
    构造总入流时间权重(config).to_csv(
        结果目录 / "0325_八小时降雨权重.csv",
        index=False,
        encoding="utf-8-sig",
    )
    构造总入流过程(config).to_csv(
        结果目录 / "0325_总入流过程.csv",
        index=False,
        encoding="utf-8-sig",
    )
    构造真值注水(config).to_csv(
        结果目录 / "0325_真值注水数据.csv",
        index=False,
        encoding="utf-8-sig",
    )


__all__ = [
    "实验配置",
    "项目根目录",
    "代码目录",
    "数据目录",
    "结果目录",
    "运行时数据目录",
    "基线模型路径",
    "读取_inp分段",
    "提取数据行",
    "读取坐标",
    "读取连边",
    "构造总入流时间权重",
    "构造总入流过程",
    "构造真值注水",
    "根据总体积生成节点注入序列",
    "保存基础数据",
]
