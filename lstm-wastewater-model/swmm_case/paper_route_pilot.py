from __future__ import annotations

import importlib.util
import json
import math
import shutil
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


BASE_MODULE_PATH = Path(r"E:\PY\LSTM\swmm_case\full_network_source_tracing.py")
DEFAULT_SEED = 42


def load_base_module():
    spec = importlib.util.spec_from_file_location("full_network_source_tracing", BASE_MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


base = load_base_module()
MONITOR_NODES = base.MONITOR_NODES
TRUTH_NODES = base.TRUTH_NODES


@dataclass
class Config:
    # 基础输入文件
    dry_inp: Path = Path(r"E:\PY\LSTM\swmm_case\case_dry.inp")
    inflow_workbook: Path = Path(r"E:\PY\LSTM\swmm_case\inflow_templates.xlsx")
    # 当前这版仍然使用 midscale 目录来承接主结果，避免分散
    result_dir: Path = Path(r"E:\PY\LSTM\swmm_case\paper_route_results")
    # 候选节点池规模。当前项目固定为 10 个点做受控盲测
    pilot_candidate_limit: int = 10
    # 允许的最大异常点个数，旧版组合搜索还会用到
    max_source_count: int = 3
    complexity_penalty: float = 0.025
    # 监测比较口径按小时，SWMM 内部仍用更细路由步长
    eval_stride_seconds: int = 3600
    # 将真实注水模板整体放大的系数。用于增强实验激励强度
    truth_scale_factor: float = 2.0
    scan_top_n: int = 10
    combo_refine_top_per_count: int = 3
    ga_pop_count: int = 2
    ga_pop_size: int = 6
    ga_generations: int = 3
    ga_migration_interval: int = 2
    elite_ratio: float = 0.25
    mutation_sigma: float = 0.15
    am_samples: int = 30
    am_burn_in: int = 8
    am_sigma: float = 0.08
    sigma_obs: float = 0.03
    topology_bonus: float = 0.14
    block_bonus: float = 0.10
    multi_node_block_bonus: float = 0.06
    snapshot_dir: Path = Path(r"E:\PY\LSTM\swmm_case\paper_route_results\history")

    def ensure_dirs(self) -> None:
        self.result_dir.mkdir(parents=True, exist_ok=True)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)


def nse(obs: np.ndarray, sim: np.ndarray) -> float:
    denom = float(np.sum((obs - np.mean(obs)) ** 2))
    if denom < 1e-12:
        return 1.0 if np.allclose(obs, sim) else -np.inf
    return 1.0 - float(np.sum((obs - sim) ** 2)) / denom


def frame_to_text(df: pd.DataFrame, rows: int | None = None) -> str:
    view = df.head(rows) if rows is not None else df
    if view.empty:
        return "(empty)"
    return view.to_string(index=False)


def classification_metrics(candidate_nodes: list[str], truth_nodes: set[str], predicted_nodes: set[str]) -> dict[str, float]:
    tp = sum(1 for node in candidate_nodes if node in truth_nodes and node in predicted_nodes)
    tn = sum(1 for node in candidate_nodes if node not in truth_nodes and node not in predicted_nodes)
    fp = sum(1 for node in candidate_nodes if node not in truth_nodes and node in predicted_nodes)
    fn = sum(1 for node in candidate_nodes if node in truth_nodes and node not in predicted_nodes)
    total = max(len(candidate_nodes), 1)
    acc = (tp + tn) / total
    denom = math.sqrt(max((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn), 1e-12))
    mcc = ((tp * tn) - (fp * fn)) / denom if denom > 0 else 0.0
    return {"tp": tp, "tn": tn, "fp": fp, "fn": fn, "acc": acc, "mcc": mcc}


class PaperEvaluator:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.nodes_df, self.links_df = base.parse_network(config.dry_inp)
        self.sim_times = base.simulation_times(config.dry_inp, config.eval_stride_seconds)
        self.sim_minutes = ((self.sim_times["time"] - self.sim_times["time"].iloc[0]).dt.total_seconds() / 60.0).to_numpy()
        self.truth_templates, self.common_pattern = base.load_truth_templates(config.inflow_workbook, self.sim_minutes)
        # 这里统一对 3 个真实注水点做缩放。
        # 这样后续 dry / truth / 反演 / 评估全部共用同一套“放大后的真实工况”，
        # 不会出现训练和验证口径不一致的问题。
        if config.truth_scale_factor != 1.0:
            self.truth_templates = {
                node: values * config.truth_scale_factor for node, values in self.truth_templates.items()
            }
            self.common_pattern = sum(self.truth_templates.values())
        self.candidate_nodes = base.build_candidate_nodes(
            self.nodes_df,
            self.links_df,
            base.Config(pilot_mode=True, pilot_candidate_limit=config.pilot_candidate_limit),
        )
        self.cache: dict[tuple[str, ...], dict[str, object]] = {}
        self.single_node_cache: dict[str, dict[str, object]] = {}
        self.graph = self._build_graph()
        self.monitor_distance = self._bfs_distance(list(MONITOR_NODES))
        self.block_owner = self._multi_source_owner(list(MONITOR_NODES))

        self.dry_series = base.run_dynamic_simulation(
            str(config.dry_inp),
            config.eval_stride_seconds,
            MONITOR_NODES,
            None,
            False,
            None,
            None,
        )
        self.truth_series = base.run_dynamic_simulation(
            str(config.dry_inp),
            config.eval_stride_seconds,
            MONITOR_NODES,
            self.truth_templates,
            False,
            None,
            None,
        )
        self.observed_delta = base.make_delta(self.truth_series["metrics"], self.dry_series["metrics"])
        self.obs_flow = {monitor: self.observed_delta[f"{monitor}_inflow"].to_numpy() for monitor in MONITOR_NODES}

    def _build_graph(self) -> dict[str, set[str]]:
        graph: dict[str, set[str]] = defaultdict(set)
        for _, row in self.links_df.iterrows():
            graph[row["from_node"]].add(row["to_node"])
            graph[row["to_node"]].add(row["from_node"])
        return graph

    def _bfs_distance(self, starts: list[str]) -> dict[str, int]:
        dist = {node: 0 for node in starts}
        queue = deque(starts)
        while queue:
            node = queue.popleft()
            for nxt in self.graph.get(node, set()):
                if nxt in dist:
                    continue
                dist[nxt] = dist[node] + 1
                queue.append(nxt)
        return dist

    def _multi_source_owner(self, starts: list[str]) -> dict[str, str]:
        owner = {node: node for node in starts}
        queue = deque(starts)
        while queue:
            node = queue.popleft()
            block = owner[node]
            for nxt in sorted(self.graph.get(node, set())):
                if nxt in owner:
                    continue
                owner[nxt] = block
                queue.append(nxt)
        return owner

    def combo_topology_bonus(self, combo: list[str]) -> float:
        if len(combo) <= 1:
            node = combo[0]
            return 1.0 / (1.0 + float(self.monitor_distance.get(node, 999)))
        pairwise = []
        for i, left in enumerate(combo):
            for right in combo[i + 1 :]:
                pairwise.append(abs(self.monitor_distance.get(left, 999) - self.monitor_distance.get(right, 999)))
        avg_pairwise = float(np.mean(pairwise)) if pairwise else 0.0
        avg_monitor = float(np.mean([self.monitor_distance.get(node, 999) for node in combo]))
        return (avg_pairwise / (1.0 + avg_pairwise)) + (1.0 / (1.0 + avg_monitor))

    def combo_block_bonus(self, combo: list[str]) -> float:
        blocks = [self.block_owner.get(node, "UNASSIGNED") for node in combo]
        unique_blocks = len(set(blocks))
        counts = pd.Series(blocks).value_counts()
        has_major_plus_minor = len(combo) >= 3 and unique_blocks >= 2 and counts.max() >= 2
        return float(unique_blocks >= 2) + (1.0 if has_major_plus_minor else 0.0)

    def evaluate_plan(self, node_names: list[str], shares: np.ndarray) -> dict[str, object]:
        shares = np.clip(np.asarray(shares, dtype=float), 1e-8, 1.0)
        shares = shares / shares.sum()
        key = tuple(node_names) + tuple(np.round(shares, 6).tolist())
        if key in self.cache:
            return self.cache[key]

        pattern_sum = max(float(np.sum(self.common_pattern)), 1e-8)
        injections = {
            node: self.common_pattern * (share * pattern_sum)
            for node, share in zip(node_names, shares)
        }
        sim_series = base.run_dynamic_simulation(
            str(self.config.dry_inp),
            self.config.eval_stride_seconds,
            MONITOR_NODES,
            injections,
            False,
            None,
            None,
        )
        delta = base.make_delta(sim_series["metrics"], self.dry_series["metrics"])
        sim_flow = {monitor: delta[f"{monitor}_inflow"].to_numpy() for monitor in MONITOR_NODES}
        nse_values = [nse(self.obs_flow[monitor], sim_flow[monitor]) for monitor in MONITOR_NODES]
        mean_nse = float(np.mean(nse_values))
        sse = float(sum(np.sum((self.obs_flow[monitor] - sim_flow[monitor]) ** 2) for monitor in MONITOR_NODES))
        loss = 1.0 - mean_nse
        result = {
            "nodes": node_names,
            "shares": shares,
            "delta": delta,
            "mean_nse": mean_nse,
            "loss": loss,
            "sse": sse,
            "nse_values": nse_values,
        }
        self.cache[key] = result
        return result


def run_single_scan(evaluator: PaperEvaluator) -> pd.DataFrame:
    rows = []
    for node in evaluator.candidate_nodes:
        result = evaluator.evaluate_plan([node], np.array([1.0], dtype=float))
        evaluator.single_node_cache[node] = result
        rows.append(
            {
                "node": node,
                "loss": result["loss"],
                "mean_nse": result["mean_nse"],
                "sse": result["sse"],
                "is_truth": node in TRUTH_NODES,
            }
        )
    scan_df = pd.DataFrame(rows).sort_values("loss").reset_index(drop=True)
    scan_df["rank"] = np.arange(1, len(scan_df) + 1)
    return scan_df


def ga_search(evaluator: PaperEvaluator, candidate_nodes: list[str], config: Config) -> tuple[dict[str, object], pd.DataFrame]:
    populations = [base.dirichlet_population(config.ga_pop_size, len(candidate_nodes)) for _ in range(config.ga_pop_count)]
    elite_count = max(2, int(config.ga_pop_size * config.elite_ratio))
    history_rows = []
    best = None

    for generation in range(config.ga_generations):
        print(f"[Paper GA] generation {generation + 1}/{config.ga_generations}", flush=True)
        next_populations = []
        for population in populations:
            evaluated = [evaluator.evaluate_plan(candidate_nodes, shares) for shares in population]
            evaluated.sort(key=lambda item: item["loss"])
            if best is None or evaluated[0]["loss"] < best["loss"]:
                best = evaluated[0]
            history_rows.append(
                {
                    "generation": generation + 1,
                    "best_loss": evaluated[0]["loss"],
                    "best_mean_nse": evaluated[0]["mean_nse"],
                    "nodes": "|".join(candidate_nodes),
                }
            )

            elites = [item["shares"] for item in evaluated[:elite_count]]
            new_population = elites.copy()
            while len(new_population) < config.ga_pop_size:
                parents = np.random.choice(len(elites), size=2, replace=True)
                alpha = np.random.rand()
                child = alpha * elites[parents[0]] + (1.0 - alpha) * elites[parents[1]]
                log_child = np.log(np.clip(child, 1e-8, 1.0))
                log_child = log_child + np.random.normal(0.0, config.mutation_sigma, size=len(child))
                shifted = log_child - np.max(log_child)
                child = np.exp(shifted)
                child = child / child.sum()
                new_population.append(child)
            next_populations.append(new_population[: config.ga_pop_size])

        populations = next_populations
        if (generation + 1) % config.ga_migration_interval == 0 and best is not None:
            for population in populations[1:]:
                population[0] = best["shares"]

    history_df = pd.DataFrame(history_rows)
    return best, history_df


def am_sampling(evaluator: PaperEvaluator, node_names: list[str], start_shares: np.ndarray, config: Config) -> pd.DataFrame:
    current = evaluator.evaluate_plan(node_names, start_shares)
    current_log_like = -current["sse"] / (2.0 * config.sigma_obs ** 2)
    accepted = 0
    cov = np.eye(len(node_names)) * (config.am_sigma ** 2)
    rows = []

    for idx in range(config.am_samples):
        proposal = np.random.multivariate_normal(current["shares"], cov)
        proposal = np.clip(proposal, 1e-8, None)
        proposal = proposal / proposal.sum()
        candidate = evaluator.evaluate_plan(node_names, proposal)
        candidate_log_like = -candidate["sse"] / (2.0 * config.sigma_obs ** 2)
        beta = min(1.0, math.exp(candidate_log_like - current_log_like))
        if np.random.rand() < beta:
            current = candidate
            current_log_like = candidate_log_like
            accepted += 1
        accepted_rate = accepted / (idx + 1)
        rows.append(
            {
                "iteration": idx + 1,
                "accepted_rate": accepted_rate,
                "log_like": current_log_like,
                **{node: share for node, share in zip(node_names, current["shares"])},
            }
        )
        if idx >= 1:
            share_matrix = np.array([[row[node] for node in node_names] for row in rows], dtype=float)
            cov = np.cov(share_matrix.T) + np.eye(len(node_names)) * 1e-6

    return pd.DataFrame(rows)


def search_variable_source_count(evaluator: PaperEvaluator, candidate_nodes: list[str], config: Config) -> tuple[dict[str, object], pd.DataFrame]:
    coarse_rows = []
    for source_count in range(1, min(config.max_source_count, len(candidate_nodes)) + 1):
        for combo in combinations(candidate_nodes, source_count):
            coarse_loss = float(np.mean([evaluator.single_node_cache[node]["loss"] for node in combo]))
            topology_bonus = evaluator.combo_topology_bonus(list(combo))
            block_bonus = evaluator.combo_block_bonus(list(combo))
            penalized_coarse_loss = (
                coarse_loss
                + config.complexity_penalty * source_count
                - config.topology_bonus * topology_bonus
                - config.block_bonus * float(block_bonus >= 1.0)
                - config.multi_node_block_bonus * float(block_bonus >= 2.0)
            )
            coarse_rows.append(
                {
                    "source_count": source_count,
                    "nodes": "|".join(combo),
                    "coarse_loss": coarse_loss,
                    "topology_bonus": topology_bonus,
                    "block_bonus": block_bonus,
                    "penalized_coarse_loss": penalized_coarse_loss,
                }
            )

    coarse_df = pd.DataFrame(coarse_rows).sort_values("penalized_coarse_loss").reset_index(drop=True)
    refine_df = (
        coarse_df.groupby("source_count", group_keys=False)
        .head(config.combo_refine_top_per_count)
        .reset_index(drop=True)
    )
    refine_rows = []
    best = None
    for idx, row in refine_df.iterrows():
        combo = row["nodes"].split("|")
        print(f"[Paper combo refine] {idx + 1}/{len(refine_df)} {combo}", flush=True)
        best_ga, _ = ga_search(evaluator, combo, config)
        penalized_loss = best_ga["loss"] + config.complexity_penalty * len(combo)
        refine_rows.append(
            {
                "rank": idx + 1,
                "source_count": len(combo),
                "nodes": row["nodes"],
                "coarse_loss": row["coarse_loss"],
                "refined_loss": best_ga["loss"],
                "mean_nse": best_ga["mean_nse"],
                "penalized_loss": penalized_loss,
            }
        )
        if best is None or penalized_loss < best["penalized_loss"]:
            best = {"nodes": combo, "result": best_ga, "penalized_loss": penalized_loss}

    combo_df = pd.DataFrame(refine_rows).sort_values("penalized_loss").reset_index(drop=True)
    return best, combo_df


def build_monitor_dashboard(obs_delta: pd.DataFrame, fit_delta: pd.DataFrame, output_html: Path) -> None:
    fig = make_subplots(
        rows=len(MONITOR_NODES),
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=[f"{monitor} flow" for monitor in MONITOR_NODES],
    )
    for row_index, monitor in enumerate(MONITOR_NODES, start=1):
        fig.add_trace(
            go.Scatter(
                x=obs_delta["time"],
                y=obs_delta[f"{monitor}_inflow"],
                name=f"{monitor} observed",
                line=dict(color="#ea580c"),
            ),
            row=row_index,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=fit_delta["time"],
                y=fit_delta[f"{monitor}_inflow"],
                name=f"{monitor} simulated",
                line=dict(color="#16a34a", dash="dash"),
            ),
            row=row_index,
            col=1,
        )
    fig.update_layout(
        title="Paper-route pilot monitor flow fit",
        template="plotly_white",
        height=260 * len(MONITOR_NODES),
    )
    fig.write_html(str(output_html), include_plotlyjs="cdn")


def save_snapshot(config: Config, summary: dict[str, object], artifact_paths: list[Path]) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = config.snapshot_dir / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    for path in artifact_paths:
        if path.exists():
            shutil.copy2(path, run_dir / path.name)
    return run_dir


def main() -> None:
    np.random.seed(DEFAULT_SEED)
    config = Config()
    config.ensure_dirs()
    evaluator = PaperEvaluator(config)

    print("[Run] paper-route single scan", flush=True)
    scan_df = run_single_scan(evaluator)
    top_candidates = scan_df.head(config.scan_top_n)["node"].tolist()

    print("[Run] paper-route variable source count search", flush=True)
    best_combo, combo_df = search_variable_source_count(evaluator, top_candidates, config)
    chosen_nodes = best_combo["nodes"]
    ga_best = best_combo["result"]
    truth_combo_result = evaluator.evaluate_plan(TRUTH_NODES, np.full(len(TRUTH_NODES), 1.0 / len(TRUTH_NODES)))

    posterior = am_sampling(evaluator, chosen_nodes, ga_best["shares"], config)
    tail = posterior.iloc[config.am_burn_in :].reset_index(drop=True)
    mean_shares = np.array([tail[node].mean() for node in chosen_nodes], dtype=float)
    mean_shares = mean_shares / mean_shares.sum()
    final_result = evaluator.evaluate_plan(chosen_nodes, mean_shares)

    predicted_nodes = set(chosen_nodes)
    metrics = classification_metrics(evaluator.candidate_nodes, set(TRUTH_NODES), predicted_nodes)
    truth_share_map = {
        node: float(np.sum(evaluator.truth_templates[node])) / max(float(np.sum(evaluator.common_pattern)), 1e-8)
        for node in TRUTH_NODES
    }
    pred_share_map = {node: share for node, share in zip(chosen_nodes, final_result["shares"])}
    eval_nodes = sorted(set(TRUTH_NODES) | set(chosen_nodes))
    mae = float(np.mean([abs(pred_share_map.get(node, 0.0) - truth_share_map.get(node, 0.0)) for node in eval_nodes]))

    weights_df = pd.DataFrame(
        {
            "node": chosen_nodes,
            "estimated_share": final_result["shares"],
            "p05_share": [tail[node].quantile(0.05) for node in chosen_nodes],
            "p95_share": [tail[node].quantile(0.95) for node in chosen_nodes],
            "is_truth": [node in TRUTH_NODES for node in chosen_nodes],
        }
    ).sort_values("estimated_share", ascending=False).reset_index(drop=True)

    summary = {
        "candidate_count": len(evaluator.candidate_nodes),
        "truth_nodes": TRUTH_NODES,
        "chosen_nodes": chosen_nodes,
        "chosen_source_count": len(chosen_nodes),
        "final_loss_ga": float(final_result["loss"]),
        "final_mean_nse": float(final_result["mean_nse"]),
        "final_sse": float(final_result["sse"]),
        "complexity_penalty": config.complexity_penalty,
        "am_accept_rate": float(posterior["accepted_rate"].iloc[-1]),
        "acc": metrics["acc"],
        "mcc": metrics["mcc"],
        "mae": mae,
        "truth_combo_mean_nse_equal_share": float(truth_combo_result["mean_nse"]),
        "truth_combo_sse_equal_share": float(truth_combo_result["sse"]),
        "truth_scan_ranks": scan_df.loc[scan_df["is_truth"], ["node", "rank", "mean_nse"]].to_dict(orient="records"),
    }

    tech_doc = f"""# Paper-Route Pilot Technical Note
## 1. Current setup

- GA objective: mean NSE on monitor inflow series
- AM objective: Gaussian likelihood from flow squared error
- Active source count: unknown, searched over 1..{config.max_source_count}
- Observation channel: monitor inflow only

## 2. Summary

{json.dumps(summary, indent=2, ensure_ascii=False)}

## 3. Single-node scan Top 10

{frame_to_text(scan_df, rows=10)}

## 4. Combination search

{frame_to_text(combo_df)}

## 5. Final weights

{frame_to_text(weights_df)}
"""
    report_doc = f"""# Paper-Route Pilot Report

- Truth nodes: {", ".join(TRUTH_NODES)}
- Chosen nodes: {", ".join(chosen_nodes)}
- Mean NSE: {summary["final_mean_nse"]:.4f}
- ACC: {summary["acc"]:.4f}
- MCC: {summary["mcc"]:.4f}
- MAE: {summary["mae"]:.4f}
"""

    (config.result_dir / "paper_route_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    scan_df.to_csv(config.result_dir / "paper_route_single_scan.csv", index=False, encoding="utf-8-sig")
    combo_df.to_csv(config.result_dir / "paper_route_combo_search.csv", index=False, encoding="utf-8-sig")
    weights_df.to_csv(config.result_dir / "paper_route_weights.csv", index=False, encoding="utf-8-sig")
    posterior.to_csv(config.result_dir / "paper_route_am_samples.csv", index=False, encoding="utf-8-sig")
    final_result["delta"].to_csv(config.result_dir / "paper_route_fitted_delta.csv", index=False, encoding="utf-8-sig")
    evaluator.observed_delta.to_csv(config.result_dir / "paper_route_truth_delta.csv", index=False, encoding="utf-8-sig")
    (config.result_dir / "paper_route_technical_note.md").write_text(tech_doc, encoding="utf-8")
    (config.result_dir / "paper_route_report.md").write_text(report_doc, encoding="utf-8")
    build_monitor_dashboard(
        evaluator.observed_delta,
        final_result["delta"],
        config.result_dir / "paper_route_monitor_fit.html",
    )
    snapshot_dir = save_snapshot(
        config,
        summary,
        [
            config.result_dir / "paper_route_summary.json",
            config.result_dir / "paper_route_single_scan.csv",
            config.result_dir / "paper_route_combo_search.csv",
            config.result_dir / "paper_route_weights.csv",
            config.result_dir / "paper_route_am_samples.csv",
            config.result_dir / "paper_route_fitted_delta.csv",
            config.result_dir / "paper_route_truth_delta.csv",
            config.result_dir / "paper_route_monitor_fit.html",
        ],
    )

    print("Paper-route results:", config.result_dir)
    print("Paper-route snapshot:", snapshot_dir)
    print(weights_df.to_string(index=False))
    print(summary)


if __name__ == "__main__":
    main()
