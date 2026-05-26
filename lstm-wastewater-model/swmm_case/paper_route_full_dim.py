from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

import paper_route_pilot as pilot


DEFAULT_SEED = 42


@dataclass
class Config:
    # 结果目录。最终所有主线产物都会写到这里或其子目录
    result_dir: Path = Path(r"E:\PY\LSTM\swmm_case\paper_route_full_dim_results")
    # 10 节点受控盲测
    pilot_candidate_limit: int = 10
    # 监测比较时间分辨率：1 小时
    eval_stride_seconds: int = 3600
    # 将真实注水模板整体放大，增强可辨识性
    truth_scale_factor: float = 2.0
    # GA 参数先保持小规模，保证 PyCharm 可较快跑通
    ga_pop_count: int = 2
    ga_pop_size: int = 8
    ga_generations: int = 5
    ga_migration_interval: int = 2
    elite_ratio: float = 0.25
    mutation_sigma: float = 0.12
    initial_ppd_keep_ratio: float = 0.50
    prior_component_scale: float = 0.75
    am_samples: int = 80
    am_burn_in: int = 20
    am_sigma: float = 0.05
    adaptive_start: int = 12
    am_eps: float = 1e-6
    am_scale_override: float | None = None
    sigma_obs: float = 0.03
    tau_floor: float = 0.03
    tau_cap: float = 0.20

    def ensure_dirs(self) -> None:
        self.result_dir.mkdir(parents=True, exist_ok=True)


def project_to_simplex(raw: np.ndarray) -> np.ndarray:
    """把任意向量投影回合法份额空间。

    这一步是整个项目里非常关键的基础约束：
    1. 所有节点分到的份额不能为负；
    2. 所有节点份额之和必须等于 1；
    3. 最终再乘总入流量 Q_R，就得到满足总量守恒的节点入流量。

    无论是 GA 交叉/变异后的子代，还是 AM 高斯提议后的新样本，
    都必须经过这一步，否则就会破坏“总入流量守恒”的物理约束。
    """
    values = np.maximum(np.asarray(raw, dtype=float), 0.0)
    total = float(values.sum())
    if total <= 1e-12:
        return np.full(len(values), 1.0 / len(values))
    return values / total


def seeded_population(scan_df: pd.DataFrame, node_names: list[str], pop_size: int) -> np.ndarray:
    """利用单井扫描结果初始化 GA 种群。

    逻辑不是完全随机起跑，而是：
    1. 先把单井响应较好的节点做成“尖峰种子”；
    2. 再把靠前节点做一些组合混合作为“组合种子”；
    3. 最后再补少量 Dirichlet 随机个体。

    这样做的好处是：
    - 让 GA 一开始就更靠近高相关区域；
    - 避免 10 维全空间随机搜索过慢；
    - 同时又保留少量随机性，防止种群完全塌缩。
    """
    top = scan_df.sort_values("rank").copy()
    score = top["mean_nse"].to_numpy(dtype=float)
    score = score - np.min(score)
    score = score + 1e-3
    score = score / score.sum()
    node_to_idx = {node: idx for idx, node in enumerate(node_names)}

    seeds = []
    for _, row in top.head(min(5, len(top))).iterrows():
        vec = np.zeros(len(node_names), dtype=float)
        vec[node_to_idx[row["node"]]] = 1.0
        seeds.append(project_to_simplex(vec))

    top_nodes = top.head(min(5, len(top)))["node"].tolist()
    for k in range(2, min(5, len(top_nodes)) + 1):
        vec = np.zeros(len(node_names), dtype=float)
        chosen = top_nodes[:k]
        for node in chosen:
            vec[node_to_idx[node]] = 1.0
        seeds.append(project_to_simplex(vec))

    weighted = np.zeros(len(node_names), dtype=float)
    for _, row in top.iterrows():
        weighted[node_to_idx[row["node"]]] = float(row["mean_nse"] - top["mean_nse"].min() + 1e-3)
    seeds.append(project_to_simplex(weighted))

    while len(seeds) < pop_size:
        seeds.append(np.random.dirichlet(np.maximum(weighted, 1e-3)))
    return np.array(seeds[:pop_size])


def multivariate_logpdf(x: np.ndarray, mean: np.ndarray, cov: np.ndarray) -> float:
    dim = len(x)
    cov = np.asarray(cov, dtype=float) + np.eye(dim) * 1e-9
    mean = np.asarray(mean, dtype=float)
    x = np.asarray(x, dtype=float)
    sign, logdet = np.linalg.slogdet(cov)
    if sign <= 0:
        cov = cov + np.eye(dim) * 1e-6
        sign, logdet = np.linalg.slogdet(cov)
    inv_cov = np.linalg.inv(cov)
    diff = x - mean
    quad = float(diff.T @ inv_cov @ diff)
    return -0.5 * (dim * math.log(2.0 * math.pi) + logdet + quad)


def logsumexp(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    vmax = float(np.max(values))
    return vmax + math.log(float(np.sum(np.exp(values - vmax))))


def build_prior_model(initial_ppd_df: pd.DataFrame, node_names: list[str], config: Config) -> dict[str, object]:
    """由 initial PPD 构造混合先验。

    这里不再用“单个高斯先验”去粗暴近似 GA 结果，
    而是保留 initial PPD 的多样性：
    - 每个 initial PPD 样本都作为一个局部先验中心；
    - 轮盘赌概率作为该样本的先验权重；
    - 所有局部核叠加成混合先验。

    这样更贴近英文论文里“GA 先形成初始概率分布，再交给 AM”的思路。
    """
    samples = initial_ppd_df[node_names].to_numpy(dtype=float)
    if "roulette_probability" in initial_ppd_df.columns:
        weights = initial_ppd_df["roulette_probability"].to_numpy(dtype=float)
        weights = weights / weights.sum()
    else:
        weights = np.full(len(samples), 1.0 / max(len(samples), 1))
    if len(samples) >= 2:
        sample_cov = np.cov(samples.T) + np.eye(len(node_names)) * 1e-6
    else:
        sample_cov = np.eye(len(node_names)) * (config.am_sigma ** 2)
    component_cov = sample_cov * config.prior_component_scale + np.eye(len(node_names)) * 1e-6
    return {
        "samples": samples,
        "weights": weights,
        "component_cov": component_cov,
        "mean": np.average(samples, axis=0, weights=weights),
    }


def prior_logpdf(x: np.ndarray, prior_model: dict[str, object]) -> float:
    samples = np.asarray(prior_model["samples"], dtype=float)
    weights = np.asarray(prior_model["weights"], dtype=float)
    component_cov = np.asarray(prior_model["component_cov"], dtype=float)
    component_logs = np.array(
        [
            math.log(max(weight, 1e-12)) + multivariate_logpdf(x, mean, component_cov)
            for mean, weight in zip(samples, weights)
        ],
        dtype=float,
    )
    return logsumexp(component_logs)


def adaptive_covariance(history: np.ndarray, dim: int, eps: float, scale: float) -> np.ndarray:
    """按论文形式更新自适应协方差。

    C_n = sd * Cov(history) + sd * eps * I

    其中 sd 当前采用 2.42 / d。
    这一步决定 AM 下一步“往哪个方向动、动多大”。
    """
    if len(history) < 2:
        return np.eye(dim) * (scale * eps)
    cov = np.cov(history.T)
    cov = np.asarray(cov, dtype=float)
    if cov.ndim == 0:
        cov = np.eye(dim) * float(cov)
    return scale * cov + scale * eps * np.eye(dim)


def build_initial_ppd(merged_df: pd.DataFrame, config: Config) -> pd.DataFrame:
    """从 GA 末代群体构造 initial PPD。

    当前实现流程：
    1. 合并末代多种群个体；
    2. 按 mean_nse 转成 fitness；
    3. 由 fitness 归一化得到轮盘赌概率；
    4. 按概率抽取一批样本，形成 initial PPD。

    这一步比“只取 ga_best”更贴论文，也更有利于保留多个高概率区域。
    """
    keep_count = max(4, int(len(merged_df) * config.initial_ppd_keep_ratio))
    scored = merged_df.copy()
    fitness = scored["mean_nse"].to_numpy(dtype=float)
    fitness = fitness - np.min(fitness) + 1e-6
    probability = fitness / fitness.sum()
    scored["roulette_probability"] = probability

    sample_size = min(keep_count, len(scored))
    chosen_idx = np.random.choice(
        scored.index.to_numpy(),
        size=sample_size,
        replace=False,
        p=probability,
    )
    selected = scored.loc[chosen_idx].copy()
    selected = selected.sort_values(["mean_nse", "loss"], ascending=[False, True]).reset_index(drop=True)
    selected["ppd_rank"] = np.arange(1, len(selected) + 1)
    return selected


def ga_search_full_dim(
    evaluator: pilot.PaperEvaluator, scan_df: pd.DataFrame, config: Config
) -> tuple[dict[str, object], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """在 10 维份额空间做全局粗筛。

    每个个体代表“10 个候选节点如何分配总入流量 Q_R”。
    每次评估都会：
    1. 根据份额向量生成 10 个节点的动态注入；
    2. 调用 SWMM 做完整仿真；
    3. 取 4 个监测点的流量增量；
    4. 计算 mean NSE；
    5. 用 loss = 1 - mean NSE 排序。

    返回值里会同时保留：
    - 最佳个体 ga_best
    - 每代最佳历史 ga_history
    - 末代合并群体 merged_df
    - 全代群体明细 all_generation_df
    """
    dim = len(evaluator.candidate_nodes)
    populations = [seeded_population(scan_df, evaluator.candidate_nodes, config.ga_pop_size)]
    while len(populations) < config.ga_pop_count:
        populations.append(pilot.base.dirichlet_population(config.ga_pop_size, dim))
    elite_count = max(2, int(config.ga_pop_size * config.elite_ratio))
    best = None
    rows = []
    all_generation_records: list[dict[str, object]] = []
    last_generation_records: list[dict[str, object]] = []

    for generation in range(config.ga_generations):
        print(f"[Full-dim GA] generation {generation + 1}/{config.ga_generations}", flush=True)
        next_pops = []
        generation_records: list[dict[str, object]] = []
        for pop_idx, population in enumerate(populations, start=1):
            evaluated = [evaluator.evaluate_plan(evaluator.candidate_nodes, shares) for shares in population]
            evaluated.sort(key=lambda item: item["loss"])
            for rank, item in enumerate(evaluated, start=1):
                generation_records.append(
                    {
                        "generation": generation + 1,
                        "population": pop_idx,
                        "population_rank": rank,
                        "loss": float(item["loss"]),
                        "mean_nse": float(item["mean_nse"]),
                        "sse": float(item["sse"]),
                        **{
                            node: float(item["shares"][idx])
                            for idx, node in enumerate(evaluator.candidate_nodes)
                        },
                    }
                )
            all_generation_records.extend(generation_records[-len(evaluated):])
            if best is None or evaluated[0]["loss"] < best["loss"]:
                best = evaluated[0]
            elites = [item["shares"] for item in evaluated[:elite_count]]
            children = elites.copy()
            while len(children) < config.ga_pop_size:
                pa = elites[np.random.randint(0, len(elites))]
                pb = elites[np.random.randint(0, len(elites))]
                child = project_to_simplex(
                    0.5 * pa + 0.5 * pb + np.random.normal(0.0, config.mutation_sigma, size=dim)
                )
                children.append(child)
            next_pops.append(np.array(children))
        if best is not None and (generation + 1) % config.ga_migration_interval == 0:
            for population in next_pops[1:]:
                population[0] = best["shares"]
        rows.append(
            {
                "generation": generation + 1,
                "best_loss": float(best["loss"]),
                "best_mean_nse": float(best["mean_nse"]),
                **{node: float(best["shares"][idx]) for idx, node in enumerate(evaluator.candidate_nodes)},
                }
            )
        populations = next_pops
        last_generation_records = generation_records

    merged_df = pd.DataFrame(last_generation_records)
    all_generation_df = pd.DataFrame(all_generation_records)
    initial_ppd_df = build_initial_ppd(merged_df, config)
    return best, pd.DataFrame(rows), merged_df, all_generation_df, initial_ppd_df


def am_full_dim(evaluator: pilot.PaperEvaluator, initial_ppd_df: pd.DataFrame, config: Config) -> pd.DataFrame:
    """在 initial PPD 基础上做后验采样。

    这里的 posterior 由两部分组成：
    - prior：来自 GA 形成的 initial PPD 混合先验
    - likelihood：来自监测流量误差的高斯似然

    采样流程：
    1. 从 initial PPD 中选一个较优样本作为起点；
    2. 用多元高斯提出新方案；
    3. 投影回 simplex，保证总量守恒；
    4. 计算新旧 posterior；
    5. 按接受概率决定是否保留。
    """
    node_names = evaluator.candidate_nodes
    dim = len(node_names)
    sd = config.am_scale_override if config.am_scale_override is not None else (2.42 / dim)
    prior_model = build_prior_model(initial_ppd_df, node_names, config)
    prior_cov = np.asarray(prior_model["component_cov"], dtype=float)
    start_idx = int(initial_ppd_df["mean_nse"].astype(float).idxmax())
    current_shares = project_to_simplex(initial_ppd_df.loc[start_idx, node_names].to_numpy(dtype=float))
    current = evaluator.evaluate_plan(node_names, current_shares)
    current_log_like = -current["sse"] / (2.0 * config.sigma_obs ** 2)
    current_log_prior = prior_logpdf(current_shares, prior_model)
    current_log_post = current_log_like + current_log_prior
    accepted = 0
    base_cov = sd * prior_cov + sd * config.am_eps * np.eye(dim)
    rows = []

    for step in range(config.am_samples):
        if step < config.adaptive_start or len(rows) < 2:
            cov = base_cov
        else:
            history = np.array([[row[node] for node in node_names] for row in rows], dtype=float)
            cov = adaptive_covariance(history, dim, config.am_eps, sd)

        proposal = np.random.multivariate_normal(current_shares, cov)
        proposal = project_to_simplex(proposal)
        candidate = evaluator.evaluate_plan(node_names, proposal)
        candidate_log_like = -candidate["sse"] / (2.0 * config.sigma_obs ** 2)
        candidate_log_prior = prior_logpdf(proposal, prior_model)
        candidate_log_post = candidate_log_like + candidate_log_prior
        beta = min(1.0, math.exp(candidate_log_post - current_log_post))
        if np.random.rand() < beta:
            current_shares = proposal
            current = candidate
            current_log_like = candidate_log_like
            current_log_prior = candidate_log_prior
            current_log_post = candidate_log_post
            accepted += 1
        rows.append(
            {
                "iteration": step + 1,
                "accepted_rate": accepted / (step + 1),
                "log_like": current_log_like,
                "log_prior": current_log_prior,
                "log_posterior": current_log_post,
                "proposal_scale_sd": sd,
                "cov_trace": float(np.trace(cov)),
                **{node: float(current_shares[idx]) for idx, node in enumerate(node_names)},
            }
        )

    return pd.DataFrame(rows)


def dynamic_tau(mean_shares: pd.Series, tau_floor: float, tau_cap: float) -> float:
    """根据后验均值中的最大落差自动计算阈值。"""
    sorted_values = np.sort(mean_shares.to_numpy())[::-1]
    if len(sorted_values) < 2:
        return tau_floor
    gaps = sorted_values[:-1] - sorted_values[1:]
    gap_idx = int(np.argmax(gaps))
    tau = float((sorted_values[gap_idx] + sorted_values[gap_idx + 1]) / 2.0)
    return float(np.clip(tau, tau_floor, tau_cap))


def weights_from_tail(tail: pd.DataFrame, node_names: list[str]) -> pd.DataFrame:
    """从 AM 尾部样本提取节点后验统计量。"""
    means = pd.Series({node: tail[node].mean() for node in node_names}, dtype=float)
    tau = dynamic_tau(means, 0.03, 0.20)
    weights = pd.DataFrame(
        {
            "node": node_names,
            "posterior_mean_share": [means[node] for node in node_names],
            "posterior_median_share": [tail[node].median() for node in node_names],
            "p05_share": [tail[node].quantile(0.05) for node in node_names],
            "p95_share": [tail[node].quantile(0.95) for node in node_names],
            "is_truth": [node in pilot.TRUTH_NODES for node in node_names],
        }
    ).sort_values("posterior_mean_share", ascending=False).reset_index(drop=True)
    weights["is_active"] = weights["posterior_mean_share"] >= tau
    weights["tau"] = tau
    return weights


def choose_final_solution(
    evaluator: pilot.PaperEvaluator,
    ga_best: dict[str, object],
    initial_ppd_df: pd.DataFrame,
    posterior: pd.DataFrame,
    tail: pd.DataFrame,
    node_names: list[str],
) -> tuple[dict[str, object], pd.Series]:
    """在多个代表解之间选一个最能解释监测曲线的最终方案。

    这里保留了工程上常用的几种代表方式：
    - GA 最优解
    - initial PPD 均值
    - posterior 均值
    - posterior 中位数
    - posterior 最大后验样本

    最终统一再回到 SWMM 中做一次评价，谁的 mean NSE 更高就选谁。
    """
    mean_shares = pd.Series({node: tail[node].mean() for node in node_names}, dtype=float)
    median_shares = pd.Series({node: tail[node].median() for node in node_names}, dtype=float)
    best_idx = int(posterior["log_posterior"].idxmax())
    posterior_best_series = pd.Series({node: posterior.loc[best_idx, node] for node in node_names}, dtype=float)
    initial_ppd_mean = pd.Series({node: float(initial_ppd_df[node].mean()) for node in node_names}, dtype=float)

    candidates = [
        ("ga_best", pd.Series(ga_best["shares"], index=node_names, dtype=float)),
        ("initial_ppd_mean", initial_ppd_mean),
        ("posterior_mean", mean_shares),
        ("posterior_median", median_shares),
        ("posterior_best", posterior_best_series),
    ]
    best_name = ""
    best_result = None
    best_series = None
    for name, series in candidates:
        shares = project_to_simplex(series.to_numpy())
        result = evaluator.evaluate_plan(node_names, shares)
        if best_result is None or result["mean_nse"] > best_result["mean_nse"]:
            best_name = name
            best_result = result
            best_series = pd.Series(shares, index=node_names, dtype=float)
    assert best_result is not None and best_series is not None
    best_result["solution_name"] = best_name
    return best_result, best_series


def build_posterior_bar(weights_df: pd.DataFrame, output_html: Path) -> None:
    colors = ["#dc2626" if truth else "#64748b" for truth in weights_df["is_truth"]]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=weights_df["node"],
            y=weights_df["posterior_mean_share"],
            marker_color=colors,
            error_y=dict(
                type="data",
                symmetric=False,
                array=weights_df["p95_share"] - weights_df["posterior_mean_share"],
                arrayminus=weights_df["posterior_mean_share"] - weights_df["p05_share"],
            ),
            customdata=weights_df[["is_truth", "is_active"]].to_numpy(),
            hovertemplate="节点=%{x}<br>后验均值=%{y:.4f}<br>真值=%{customdata[0]}<br>判为异常=%{customdata[1]}<extra></extra>",
        )
    )
    fig.update_layout(
        title="10 维后验分布均值与区间",
        template="plotly_white",
        xaxis_title="候选节点",
        yaxis_title="Posterior mean share",
        height=520,
    )
    fig.write_html(str(output_html), include_plotlyjs="cdn")


def build_convergence_figure(ga_history: pd.DataFrame, am_df: pd.DataFrame, output_html: Path) -> None:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=ga_history["generation"],
            y=ga_history["best_mean_nse"],
            mode="lines+markers",
            name="GA best mean NSE",
            line=dict(color="#2563eb", width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=am_df["iteration"],
            y=am_df["accepted_rate"],
            mode="lines",
            name="AM accepted rate",
            yaxis="y2",
            line=dict(color="#16a34a", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=am_df["iteration"],
            y=am_df["log_posterior"],
            mode="lines",
            name="AM log-posterior",
            yaxis="y3",
            line=dict(color="#c2410c", width=2),
        )
    )
    fig.update_layout(
        title="10 维全量反演收敛过程",
        template="plotly_white",
        xaxis_title="Iteration / Generation",
        yaxis=dict(title="GA best mean NSE"),
        yaxis2=dict(title="AM accepted rate", overlaying="y", side="right", position=0.92),
        yaxis3=dict(title="AM log-posterior", anchor="free", overlaying="y", side="right", position=1.0),
        height=540,
    )
    fig.write_html(str(output_html), include_plotlyjs="cdn")


def write_report(summary: dict[str, object], weights_df: pd.DataFrame, scan_df: pd.DataFrame, output_path: Path) -> None:
    active_nodes = weights_df.loc[weights_df["final_is_active"], "node"].tolist()
    report = f"""# 10 节点全维自由反演报告

## 通俗总结

- 这次不再先猜“几个点有问题”，而是让 10 个候选节点全部参加反演。
- 算法只遵守一条硬规则：所有节点分到的水量之和必须等于总注水量。
- 在这个约束下，GA 先找整体拟合最好的方案，AM 再做细调，最后让大多数无问题节点自动收缩到接近 0。
- 这次还加入了“单井扫描引导的 GA 初始化”，让全量反演不至于完全随机起跑。

## 当前结果

- 10 维候选节点：{", ".join(weights_df["node"].tolist())}
- 判定阈值 tau：{summary["tau"]:.4f}
- 最终解来源：{summary["final_solution_name"]}
- 识别出的异常点：{", ".join(active_nodes)}
- 真值点：{", ".join(pilot.TRUTH_NODES)}
- Mean NSE：{summary["final_mean_nse"]:.4f}
- SSE：{summary["final_sse"]:.4f}
- ACC：{summary["acc"]:.4f}
- MCC：{summary["mcc"]:.4f}
- 全向量 MAE：{summary["mae_all_nodes"]:.4f}
- 真值节点 MAE：{summary["mae_truth_nodes"]:.4f}
- AM 接受率：{summary["am_accept_rate"]:.4f}

## 详细原理

### 1. 总量硬约束

10 个节点的份额向量满足：

`share_i >= 0`

`sum(share_i) = 1`

再乘以总注水量 `Q_R` 得到每个节点的注水量。

### 2. GA 目标函数

对 4 个监测点的流量增量计算平均 NSE，最小化：

`loss_GA = 1 - mean_NSE`

为了让 10 维全量搜索更稳定，GA 初始种群不是纯随机，而是由两部分组成：

- 单井扫描靠前节点的“尖峰种子”
- 前几名节点混合形成的“组合种子”

### 3. AM 似然函数

`logL = -SSE / (2 * sigma_obs^2)`

每次提议后都做：

- 非负投影
- 重归一化到总量超平面

### 4. 自动稀疏化

根据后验均值序列中的最大 Gap 自动计算阈值 tau，
再用最终选定解的份额 `final_share >= tau` 判定异常点。

## 基础数据处理

- 基线模型：`case_dry.inp`
- 真值模板：`inflow_templates.xlsx`
- 比较口径：小时级
- SWMM 路由：30 秒
- 观测量：4 个监测点的流量增量序列

## 单井扫描参考

{scan_df.to_string(index=False)}

## 后验表

{weights_df.to_string(index=False)}
"""
    output_path.write_text(report, encoding="utf-8")


def write_overview(summary: dict[str, object], weights_df: pd.DataFrame, output_path: Path) -> None:
    active_nodes = weights_df.loc[weights_df["final_is_active"], "node"].tolist()
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>10 维全量反演总览</title>
  <style>
    body {{
      margin: 0;
      font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
      background: linear-gradient(180deg, #f6f1e8 0%, #ece3d3 100%);
      color: #16202a;
    }}
    .wrap {{ width: min(1400px, calc(100vw - 40px)); margin: 0 auto; padding: 28px 0 40px; }}
    .grid {{ display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 20px; }}
    .row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }}
    .card {{
      background: rgba(255,255,255,0.78);
      border: 1px solid rgba(22,32,42,0.10);
      border-radius: 24px;
      padding: 22px;
      box-shadow: 0 14px 40px rgba(22,32,42,0.08);
      backdrop-filter: blur(10px);
    }}
    h1 {{ margin: 0 0 10px; font-size: 38px; line-height: 1.08; }}
    h2 {{ margin: 0 0 12px; font-size: 22px; }}
    p {{ margin: 0; color: #52606d; line-height: 1.7; }}
    .kpis {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin-top: 16px; }}
    .kpi {{ border: 1px solid rgba(22,32,42,0.10); border-radius: 18px; padding: 14px; background: rgba(255,255,255,0.68); }}
    .kpi b {{ display: block; font-size: 28px; }}
    iframe {{ width: 100%; height: 620px; border: 0; border-radius: 18px; background: white; }}
    ul {{ margin: 10px 0 0 18px; color: #52606d; line-height: 1.8; }}
    @media (max-width: 1100px) {{
      .grid, .row {{ grid-template-columns: 1fr; }}
      iframe {{ height: 520px; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="grid">
      <section class="card">
        <h1>10 维全量自由反演</h1>
        <p>这版算法不再先枚举“几个点有问题”，而是让 10 个候选节点一起参与反演。它只遵守总量约束，再通过 GA 和 AM 让大多数节点自动收缩到接近 0。</p>
        <div class="kpis">
          <div class="kpi"><b>{summary["final_mean_nse"]:.4f}</b><span>Final Mean NSE</span></div>
          <div class="kpi"><b>{summary["acc"]:.4f}</b><span>ACC</span></div>
          <div class="kpi"><b>{summary["mcc"]:.4f}</b><span>MCC</span></div>
          <div class="kpi"><b>{summary["tau"]:.4f}</b><span>Dynamic Tau</span></div>
        </div>
      </section>
      <section class="card">
        <h2>当前结论</h2>
        <ul>
          <li>真值点：{", ".join(pilot.TRUTH_NODES)}</li>
          <li>识别点：{", ".join(active_nodes)}</li>
          <li>最终解来源：{summary["final_solution_name"]}</li>
          <li>总注水量 Q_R：{summary["q_r"]:.1f}</li>
          <li>全向量 MAE：{summary["mae_all_nodes"]:.4f}</li>
          <li>真值节点 MAE：{summary["mae_truth_nodes"]:.4f}</li>
        </ul>
        <p style="margin-top:14px;">这一轮已经把拟合分数显著拉高，但定位上仍有邻近井代偿。下一步要继续增强定位约束和后验判别，而不是只追求更高的拟合。</p>
      </section>
    </div>
    <div class="row">
      <section class="card">
        <h2>监测点拟合</h2>
        <iframe src="full_dim_monitor_fit.html"></iframe>
      </section>
      <section class="card">
        <h2>后验条形图</h2>
        <iframe src="full_dim_posterior_bar.html"></iframe>
      </section>
    </div>
    <div class="row">
      <section class="card">
        <h2>收敛过程</h2>
        <iframe src="full_dim_convergence.html"></iframe>
      </section>
      <section class="card">
        <h2>技术报告</h2>
        <p>详细说明见当前目录下的 <code>full_dim_report.md</code>。这份报告已经按“先通俗总结，再讲公式和数据处理”来组织。</p>
      </section>
    </div>
  </div>
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")


def main() -> None:
    """单文件运行入口。

    适合直接在 PyCharm 里运行这个脚本，快速生成一版完整结果。
    更推荐的正式入口仍然是 run_final_pipeline.py，因为它还会自动生成
    posterior 页面、领导汇报页和控制台摘要。
    """
    np.random.seed(DEFAULT_SEED)
    config = Config()
    config.ensure_dirs()

    # 这里会按照 Config 中的 truth_scale_factor 对真实注水模板整体缩放。
    evaluator = pilot.PaperEvaluator(
        pilot.Config(
            result_dir=config.result_dir,
            pilot_candidate_limit=config.pilot_candidate_limit,
            eval_stride_seconds=config.eval_stride_seconds,
            truth_scale_factor=config.truth_scale_factor,
        )
    )
    scan_df = pilot.run_single_scan(evaluator)
    q_r = float(sum(np.sum(evaluator.truth_templates[node]) for node in pilot.TRUTH_NODES) * config.eval_stride_seconds)

    ga_best, ga_history, merged_last_gen_df, all_generation_df, initial_ppd_df = ga_search_full_dim(evaluator, scan_df, config)
    posterior = am_full_dim(evaluator, initial_ppd_df, config)
    tail = posterior.iloc[config.am_burn_in :].reset_index(drop=True)
    final_result, final_series = choose_final_solution(
        evaluator,
        ga_best,
        initial_ppd_df,
        posterior,
        tail,
        evaluator.candidate_nodes,
    )
    weights_df = weights_from_tail(tail, evaluator.candidate_nodes)
    tau = float(weights_df["tau"].iloc[0])
    weights_df["final_share"] = weights_df["node"].map(final_series.to_dict())
    weights_df["final_is_active"] = weights_df["final_share"] >= tau

    predicted_nodes = set(weights_df.loc[weights_df["final_is_active"], "node"].tolist())
    metrics = pilot.classification_metrics(evaluator.candidate_nodes, set(pilot.TRUTH_NODES), predicted_nodes)
    true_share_map = {
        node: float(np.sum(evaluator.truth_templates[node])) / max(float(np.sum(evaluator.common_pattern)), 1e-8)
        for node in pilot.TRUTH_NODES
    }
    pred_share_map = final_series.to_dict()
    mae_all_nodes = float(np.mean([abs(pred_share_map.get(node, 0.0) - true_share_map.get(node, 0.0)) for node in evaluator.candidate_nodes]))
    mae_truth_nodes = float(np.mean([abs(pred_share_map.get(node, 0.0) - true_share_map.get(node, 0.0)) for node in pilot.TRUTH_NODES]))

    summary = {
        "candidate_count": len(evaluator.candidate_nodes),
        "candidate_nodes": evaluator.candidate_nodes,
        "truth_nodes": pilot.TRUTH_NODES,
        "predicted_nodes": sorted(predicted_nodes),
        "merged_last_generation_size": int(len(merged_last_gen_df)),
        "initial_ppd_size": int(len(initial_ppd_df)),
        "final_mean_nse": float(final_result["mean_nse"]),
        "final_sse": float(final_result["sse"]),
        "final_solution_name": final_result["solution_name"],
        "truth_scale_factor": config.truth_scale_factor,
        "q_r": q_r,
        "tau": tau,
        "acc": float(metrics["acc"]),
        "mcc": float(metrics["mcc"]),
        "mae_all_nodes": mae_all_nodes,
        "mae_truth_nodes": mae_truth_nodes,
        "am_accept_rate": float(posterior["accepted_rate"].iloc[-1]),
    }

    (config.result_dir / "full_dim_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    ga_history.to_csv(config.result_dir / "full_dim_ga_history.csv", index=False, encoding="utf-8-sig")
    all_generation_df.to_csv(config.result_dir / "full_dim_ga_population.csv", index=False, encoding="utf-8-sig")
    merged_last_gen_df.to_csv(config.result_dir / "full_dim_merged_last_generation.csv", index=False, encoding="utf-8-sig")
    initial_ppd_df.to_csv(config.result_dir / "full_dim_initial_ppd.csv", index=False, encoding="utf-8-sig")
    scan_df.to_csv(config.result_dir / "full_dim_single_scan.csv", index=False, encoding="utf-8-sig")
    posterior.to_csv(config.result_dir / "full_dim_am_samples.csv", index=False, encoding="utf-8-sig")
    weights_df.to_csv(config.result_dir / "full_dim_weights.csv", index=False, encoding="utf-8-sig")
    final_result["delta"].to_csv(config.result_dir / "full_dim_fitted_delta.csv", index=False, encoding="utf-8-sig")
    evaluator.observed_delta.to_csv(config.result_dir / "full_dim_truth_delta.csv", index=False, encoding="utf-8-sig")
    pilot.build_monitor_dashboard(evaluator.observed_delta, final_result["delta"], config.result_dir / "full_dim_monitor_fit.html")
    build_posterior_bar(weights_df, config.result_dir / "full_dim_posterior_bar.html")
    build_convergence_figure(ga_history, posterior, config.result_dir / "full_dim_convergence.html")
    write_report(summary, weights_df, scan_df, config.result_dir / "full_dim_report.md")
    write_overview(summary, weights_df, config.result_dir / "full_dim_overview.html")

    print("Full-dim results:", config.result_dir)
    print(weights_df.to_string(index=False))
    print(summary)


if __name__ == "__main__":
    main()
