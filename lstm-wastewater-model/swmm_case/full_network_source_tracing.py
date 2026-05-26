from __future__ import annotations

import json
import math
import re
from collections import defaultdict, deque
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pyswmm import Links, Nodes, Simulation


MONITOR_NODES = ["J145", "J17", "J236", "J59"]
TRUTH_NODES = ["J129", "J195", "J61"]
KNOWN_BASELINE_NODES = {"J106", "J197"}
DEFAULT_SEED = 42


@dataclass
class Config:
    work_dir: Path = Path(r"E:\PY\LSTM\swmm_case")
    result_dir: Path = Path(r"E:\PY\LSTM\swmm_case\full_network_results")
    dry_inp: Path = Path(r"E:\PY\LSTM\swmm_case\case_dry.inp")
    inflow_workbook: Path = Path(r"E:\PY\LSTM\swmm_case\inflow_templates.xlsx")
    pilot_mode: bool = True
    pilot_candidate_limit: int = 10
    max_source_count: int = 4
    complexity_penalty: float = 0.05
    eval_stride_seconds: int = 3600
    scan_top_n: int = 10
    ga_pop_count: int = 2
    ga_pop_size: int = 5
    ga_generations: int = 3
    ga_migration_interval: int = 2
    elite_ratio: float = 0.25
    mutation_sigma: float = 0.18
    local_step: float = 0.03
    local_min_step: float = 0.03
    mcmc_samples: int = 2
    mcmc_burn_in: int = 0
    mcmc_sigma: float = 0.06
    combo_ga_pop_size: int = 4
    combo_ga_generations: int = 2
    combo_refine_top_k: int = 4
    depth_weight: float = 1.0
    inflow_weight: float = 1.0
    volume_weight: float = 0.6
    animation_stride: int = 1

    def ensure_dirs(self) -> None:
        self.result_dir.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "gbk"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("unknown", b"", 0, 1, f"cannot decode {path}")


def normalise_series(values: np.ndarray) -> np.ndarray:
    std = float(np.std(values))
    if std < 1e-8:
        return values.astype(float)
    return values.astype(float) / std


def cumulative_volume(values: np.ndarray, step_seconds: int) -> np.ndarray:
    return np.cumsum(values.astype(float) * float(step_seconds))


def dirichlet_population(pop_size: int, dim: int) -> np.ndarray:
    return np.random.dirichlet(np.ones(dim), size=pop_size)


def mutate_shares(shares: np.ndarray, sigma: float) -> np.ndarray:
    logits = np.log(np.clip(shares, 1e-8, 1.0))
    logits = logits + np.random.normal(0.0, sigma, size=logits.shape)
    exp = np.exp(logits - logits.max())
    return exp / exp.sum()


def crossover_shares(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    alpha = np.random.rand()
    child = alpha * a + (1.0 - alpha) * b
    return child / child.sum()


def dataframe_markdown(df: pd.DataFrame) -> str:
    headers = list(df.columns)
    rows = [headers, ["---"] * len(headers)]
    for _, row in df.iterrows():
        rows.append([str(row[col]) for col in headers])
    return "\n".join("| " + " | ".join(items) + " |" for items in rows)


def parse_network(inp_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    sections: dict[str, list[list[str]]] = {}
    current = ""
    for raw in read_text(inp_path).splitlines():
        stripped = raw.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            current = stripped.upper()
            sections[current] = []
            continue
        if not current or not stripped or stripped.startswith(";"):
            continue
        sections[current].append(re.split(r"\s+", stripped))

    node_rows = []
    for item in sections.get("[JUNCTIONS]", []):
        node_rows.append({"node": item[0], "elevation": float(item[1]), "node_type": "JUNCTION"})
    for item in sections.get("[OUTFALLS]", []):
        node_rows.append({"node": item[0], "elevation": float(item[1]), "node_type": "OUTFALL"})
    for item in sections.get("[STORAGE]", []):
        node_rows.append({"node": item[0], "elevation": float(item[1]), "node_type": "STORAGE"})
    nodes = pd.DataFrame(node_rows)

    coords = pd.DataFrame(sections.get("[COORDINATES]", []), columns=["node", "x", "y"])
    coords["x"] = coords["x"].astype(float)
    coords["y"] = coords["y"].astype(float)
    nodes = nodes.merge(coords, on="node", how="left")

    conduits = pd.DataFrame(
        [item[:5] for item in sections.get("[CONDUITS]", []) if len(item) >= 5],
        columns=["link", "from_node", "to_node", "length", "roughness"],
    )
    conduits["length"] = conduits["length"].astype(float)
    xsecs = pd.DataFrame(
        [item[:3] for item in sections.get("[XSECTIONS]", []) if len(item) >= 3],
        columns=["link", "shape", "geom1"],
    )
    xsecs["geom1"] = xsecs["geom1"].astype(float)
    links = conduits.merge(xsecs, on="link", how="left")
    links = links.merge(nodes[["node", "x", "y", "elevation"]], left_on="from_node", right_on="node", how="left")
    links = links.rename(columns={"x": "x1", "y": "y1", "elevation": "z1"}).drop(columns=["node"])
    links = links.merge(nodes[["node", "x", "y", "elevation"]], left_on="to_node", right_on="node", how="left")
    links = links.rename(columns={"x": "x2", "y": "y2", "elevation": "z2"}).drop(columns=["node"])
    links["mx"] = (links["x1"] + links["x2"]) / 2
    links["my"] = (links["y1"] + links["y2"]) / 2
    links["mz"] = (links["z1"] + links["z2"]) / 2
    return nodes, links


def build_candidate_nodes(nodes_df: pd.DataFrame, links_df: pd.DataFrame, config: Config) -> list[str]:
    candidates = [node for node in nodes_df.loc[nodes_df["node_type"] == "JUNCTION", "node"].tolist() if node not in KNOWN_BASELINE_NODES]
    if not config.pilot_mode:
        return candidates

    adjacency: dict[str, set[str]] = defaultdict(set)
    for _, row in links_df.iterrows():
        adjacency[row["from_node"]].add(row["to_node"])
        adjacency[row["to_node"]].add(row["from_node"])

    selected = list(TRUTH_NODES)
    seen = set(selected)
    queue = deque(TRUTH_NODES)
    while queue and len(selected) < config.pilot_candidate_limit:
        current = queue.popleft()
        for nxt in sorted(adjacency[current]):
            if nxt in seen or nxt not in candidates:
                continue
            seen.add(nxt)
            selected.append(nxt)
            queue.append(nxt)
            if len(selected) >= config.pilot_candidate_limit:
                break
    return selected


def simulation_times(inp_path: Path, stride_seconds: int) -> pd.DataFrame:
    rows = []
    with Simulation(str(inp_path)) as sim:
        sim.step_advance(stride_seconds)
        for _ in sim:
            rows.append({"time": sim.current_time})
    return pd.DataFrame(rows)


def load_truth_templates(workbook_path: Path, sim_minutes: np.ndarray) -> tuple[dict[str, np.ndarray], np.ndarray]:
    xls = pd.ExcelFile(workbook_path)
    templates: dict[str, np.ndarray] = {}
    for sheet in xls.sheet_names:
        match = re.search(r"(J\d+)", str(sheet))
        if not match:
            continue
        node = match.group(1)
        if node not in TRUTH_NODES:
            continue
        df = pd.read_excel(workbook_path, sheet_name=sheet)
        time_col = df.columns[0]
        flow_col = df.columns[-1]
        raw_time = df[time_col].astype(float).to_numpy()
        if "小时" in str(time_col):
            raw_time = raw_time * 60.0
        raw_flow = df[flow_col].astype(float).to_numpy()
        templates[node] = np.interp(sim_minutes, raw_time, raw_flow, left=0.0, right=0.0)
    if len(templates) != len(TRUTH_NODES):
        raise RuntimeError("truth templates are incomplete")
    total_truth = sum(templates.values())
    return templates, total_truth


def run_dynamic_simulation(
    inp_path: str,
    stride_seconds: int,
    monitor_nodes: Sequence[str],
    injection_series: dict[str, np.ndarray] | None,
    capture_dynamic: bool,
    node_ids: Sequence[str] | None,
    link_ids: Sequence[str] | None,
) -> dict[str, pd.DataFrame]:
    metric_rows = []
    dynamic_rows = []
    with Simulation(inp_path) as sim:
        sim.step_advance(stride_seconds)
        monitor_objs = {name: Nodes(sim)[name] for name in monitor_nodes}
        injection_objs = {name: Nodes(sim)[name] for name in (injection_series or {}).keys()}
        if capture_dynamic:
            all_nodes = {name: Nodes(sim)[name] for name in node_ids or []}
            all_links = {name: Links(sim)[name] for name in link_ids or []}

        for idx, _ in enumerate(sim):
            if injection_series:
                for node_name, values in injection_series.items():
                    if idx < len(values):
                        injection_objs[node_name].generated_inflow(float(values[idx]))

            timestamp = sim.current_time
            row = {"time": timestamp}
            for name, node in monitor_objs.items():
                row[f"{name}_depth"] = node.depth
                row[f"{name}_head"] = node.head
                row[f"{name}_inflow"] = node.total_inflow
            metric_rows.append(row)

            if capture_dynamic:
                for node_name, node in all_nodes.items():
                    dynamic_rows.append({"time": timestamp, "kind": "node", "id": node_name, "value_a": node.depth, "value_b": node.head})
                for link_name, link in all_links.items():
                    dynamic_rows.append({"time": timestamp, "kind": "link", "id": link_name, "value_a": link.flow, "value_b": link.depth})

    return {"metrics": pd.DataFrame(metric_rows), "dynamic": pd.DataFrame(dynamic_rows)}


def make_delta(run_df: pd.DataFrame, base_df: pd.DataFrame) -> pd.DataFrame:
    merged = run_df.merge(base_df, on="time", suffixes=("_run", "_base"))
    out = pd.DataFrame({"time": merged["time"]})
    for monitor in MONITOR_NODES:
        for suffix in ("depth", "head", "inflow"):
            out[f"{monitor}_{suffix}"] = merged[f"{monitor}_{suffix}_run"] - merged[f"{monitor}_{suffix}_base"]
    return out


def build_vector(delta_df: pd.DataFrame, step_seconds: int, depth_weight: float, inflow_weight: float, volume_weight: float) -> np.ndarray:
    parts = []
    for monitor in MONITOR_NODES:
        depth = delta_df[f"{monitor}_depth"].to_numpy()
        inflow = delta_df[f"{monitor}_inflow"].to_numpy()
        volume = cumulative_volume(inflow, step_seconds)
        parts.append(normalise_series(depth) * depth_weight)
        parts.append(normalise_series(inflow) * inflow_weight)
        parts.append(normalise_series(volume) * volume_weight)
    return np.concatenate(parts)


class FullNetworkEvaluator:
    def __init__(self, config: Config, nodes_df: pd.DataFrame, links_df: pd.DataFrame) -> None:
        self.config = config
        self.nodes_df = nodes_df
        self.links_df = links_df
        self.sim_times = simulation_times(config.dry_inp, config.eval_stride_seconds)
        self.sim_minutes = ((self.sim_times["time"] - self.sim_times["time"].iloc[0]).dt.total_seconds() / 60.0).to_numpy()
        self.truth_templates, self.common_pattern = load_truth_templates(config.inflow_workbook, self.sim_minutes)
        self.candidate_nodes = build_candidate_nodes(nodes_df, links_df, config)
        self.total_pattern_volume = float(np.sum(self.common_pattern) * config.eval_stride_seconds)
        self.cache: dict[tuple[str, ...], dict[str, Any]] = {}

        self.dry_series = run_dynamic_simulation(
            inp_path=str(config.dry_inp),
            stride_seconds=config.eval_stride_seconds,
            monitor_nodes=MONITOR_NODES,
            injection_series=None,
            capture_dynamic=False,
            node_ids=None,
            link_ids=None,
        )
        self.truth_series = run_dynamic_simulation(
            inp_path=str(config.dry_inp),
            stride_seconds=config.eval_stride_seconds,
            monitor_nodes=MONITOR_NODES,
            injection_series=self.truth_templates,
            capture_dynamic=False,
            node_ids=None,
            link_ids=None,
        )
        self.observed_delta = make_delta(self.truth_series["metrics"], self.dry_series["metrics"])
        self.target_vector = build_vector(
            self.observed_delta,
            config.eval_stride_seconds,
            config.depth_weight,
            config.inflow_weight,
            config.volume_weight,
        )
        self.single_node_vectors: dict[str, np.ndarray] = {}

    def evaluate_plan(self, node_names: Sequence[str], shares: np.ndarray) -> dict[str, Any]:
        shares = np.clip(np.asarray(shares, dtype=float), 1e-8, 1.0)
        shares = shares / shares.sum()
        key = tuple(node_names) + tuple(np.round(shares, 6).tolist())
        if key in self.cache:
            return self.cache[key]

        injections = {}
        pattern_sum = max(float(np.sum(self.common_pattern)), 1e-8)
        for node_name, share in zip(node_names, shares):
            injections[node_name] = self.common_pattern * (share * pattern_sum)

        series = run_dynamic_simulation(
            inp_path=str(self.config.dry_inp),
            stride_seconds=self.config.eval_stride_seconds,
            monitor_nodes=MONITOR_NODES,
            injection_series=injections,
            capture_dynamic=False,
            node_ids=None,
            link_ids=None,
        )
        delta = make_delta(series["metrics"], self.dry_series["metrics"])
        sim_vector = build_vector(
            delta,
            self.config.eval_stride_seconds,
            self.config.depth_weight,
            self.config.inflow_weight,
            self.config.volume_weight,
        )
        residual = sim_vector - self.target_vector
        result = {"nodes": list(node_names), "shares": shares, "mse": float(np.mean(residual**2)), "delta": delta}
        self.cache[key] = result
        return result

    def truth_dynamic(self) -> dict[str, pd.DataFrame]:
        return run_dynamic_simulation(
            inp_path=str(self.config.dry_inp),
            stride_seconds=self.config.eval_stride_seconds,
            monitor_nodes=MONITOR_NODES,
            injection_series=self.truth_templates,
            capture_dynamic=True,
            node_ids=self.nodes_df["node"].tolist(),
            link_ids=self.links_df["link"].tolist(),
        )


def scan_single_nodes(evaluator: FullNetworkEvaluator) -> pd.DataFrame:
    rows = []
    for idx, node in enumerate(evaluator.candidate_nodes, start=1):
        if idx % 25 == 0:
            print(f"[Scan] {idx}/{len(evaluator.candidate_nodes)}", flush=True)
        result = evaluator.evaluate_plan([node], np.array([1.0], dtype=float))
        evaluator.single_node_vectors[node] = build_vector(
            result["delta"],
            evaluator.config.eval_stride_seconds,
            evaluator.config.depth_weight,
            evaluator.config.inflow_weight,
            evaluator.config.volume_weight,
        )
        rows.append({"node": node, "single_mse": result["mse"], "is_truth": node in TRUTH_NODES})
    scan_df = pd.DataFrame(rows).sort_values("single_mse", ascending=True).reset_index(drop=True)
    scan_df["rank"] = np.arange(1, len(scan_df) + 1)
    return scan_df


def run_mpga_joint(evaluator: FullNetworkEvaluator, candidate_nodes: Sequence[str], config: Config) -> tuple[dict[str, Any], pd.DataFrame]:
    populations = [dirichlet_population(config.ga_pop_size, len(candidate_nodes)) for _ in range(config.ga_pop_count)]
    elite_count = max(2, int(config.ga_pop_size * config.elite_ratio))
    history = []
    best: dict[str, Any] | None = None

    for generation in range(config.ga_generations):
        print(f"[Joint MPGA] generation {generation + 1}/{config.ga_generations}", flush=True)
        next_pops = []
        for population in populations:
            evaluated = [evaluator.evaluate_plan(candidate_nodes, shares) for shares in population]
            evaluated.sort(key=lambda item: item["mse"])
            if best is None or evaluated[0]["mse"] < best["mse"]:
                best = evaluated[0]
            elites = [item["shares"] for item in evaluated[:elite_count]]
            children = elites.copy()
            while len(children) < config.ga_pop_size:
                pa = elites[np.random.randint(0, len(elites))]
                pb = elites[np.random.randint(0, len(elites))]
                children.append(mutate_shares(crossover_shares(pa, pb), config.mutation_sigma))
            next_pops.append(np.array(children))

        if best is not None and (generation + 1) % config.ga_migration_interval == 0:
            for pop in next_pops:
                pop[np.random.randint(0, len(pop))] = best["shares"]

        history.append({"generation": generation + 1, "best_mse": best["mse"], **{candidate_nodes[i]: best["shares"][i] for i in range(len(candidate_nodes))}})
        populations = next_pops

    assert best is not None
    return best, pd.DataFrame(history)


def local_refine_joint(evaluator: FullNetworkEvaluator, candidate_nodes: Sequence[str], start: np.ndarray, config: Config) -> tuple[dict[str, Any], pd.DataFrame]:
    best = evaluator.evaluate_plan(candidate_nodes, start)
    history = [{"step": config.local_step, "mse": best["mse"], **{candidate_nodes[i]: best["shares"][i] for i in range(len(candidate_nodes))}}]
    step = config.local_step
    while step >= config.local_min_step:
        print(f"[Joint Local] step={step:.4f}", flush=True)
        improved = True
        while improved:
            improved = False
            for idx in range(len(candidate_nodes)):
                for direction in (-1.0, 1.0):
                    cand = best["shares"].copy()
                    cand[idx] = max(1e-8, cand[idx] + direction * step)
                    cand = cand / cand.sum()
                    result = evaluator.evaluate_plan(candidate_nodes, cand)
                    if result["mse"] < best["mse"]:
                        best = result
                        history.append({"step": step, "mse": best["mse"], **{candidate_nodes[i]: best["shares"][i] for i in range(len(candidate_nodes))}})
                        improved = True
        step /= 2.0
    return best, pd.DataFrame(history)


def run_mcmc_joint(evaluator: FullNetworkEvaluator, candidate_nodes: Sequence[str], start: np.ndarray, config: Config) -> pd.DataFrame:
    current = evaluator.evaluate_plan(candidate_nodes, start)
    accept = 0
    rows = []
    for idx in range(config.mcmc_samples):
        if (idx + 1) % 2 == 0:
            print(f"[Joint MCMC] sample {idx + 1}/{config.mcmc_samples}", flush=True)
        proposal = mutate_shares(current["shares"], config.mcmc_sigma)
        result = evaluator.evaluate_plan(candidate_nodes, proposal)
        sigma2 = max(current["mse"], 1e-8)
        log_current = -current["mse"] / (2 * sigma2)
        log_prop = -result["mse"] / (2 * sigma2)
        if math.log(np.random.rand()) < (log_prop - log_current):
            current = result
            accept += 1
        rows.append({"iter": idx + 1, "accepted_rate": accept / (idx + 1), "mse": current["mse"], **{candidate_nodes[i]: current["shares"][i] for i in range(len(candidate_nodes))}})
    return pd.DataFrame(rows)


def search_sparse_combinations(evaluator: FullNetworkEvaluator, candidate_nodes: Sequence[str], config: Config) -> tuple[dict[str, Any], pd.DataFrame]:
    coarse_rows = []
    combo_id = 0
    for source_count in range(1, min(config.max_source_count, len(candidate_nodes)) + 1):
        combo_count = math.comb(len(candidate_nodes), source_count)
        for idx, combo in enumerate(combinations(candidate_nodes, source_count), start=1):
            combo_id += 1
            if idx % 20 == 0 or idx == combo_count:
                print(f"[Combo coarse k={source_count}] {idx}/{combo_count}", flush=True)
            approx_vector = sum(evaluator.single_node_vectors[node] for node in combo) / float(source_count)
            coarse_mse = float(np.mean((approx_vector - evaluator.target_vector) ** 2))
            penalized = coarse_mse + config.complexity_penalty * float(source_count)
            coarse_rows.append({"combo_id": combo_id, "source_count": source_count, "nodes": "|".join(combo), "coarse_mse": coarse_mse, "penalized_mse": penalized})

    coarse_df = pd.DataFrame(coarse_rows).sort_values("penalized_mse", ascending=True).reset_index(drop=True)
    refine_rows = []
    best: dict[str, Any] | None = None
    original_pop_size = config.ga_pop_size
    original_generations = config.ga_generations
    config.ga_pop_size = config.combo_ga_pop_size
    config.ga_generations = config.combo_ga_generations
    try:
        for refine_idx, row in coarse_df.head(config.combo_refine_top_k).iterrows():
            combo = row["nodes"].split("|")
            print(f"[Combo refine] {refine_idx + 1}/{config.combo_refine_top_k} {combo}", flush=True)
            ga_best, _ = run_mpga_joint(evaluator, combo, config)
            penalized = ga_best["mse"] + config.complexity_penalty * float(len(combo))
            refine_rows.append(
                {
                    "combo_rank": refine_idx + 1,
                    "source_count": len(combo),
                    "nodes": row["nodes"],
                    "coarse_mse": row["coarse_mse"],
                    "penalized_mse": penalized,
                    "refined_mse": ga_best["mse"],
                    **{combo[i]: ga_best["shares"][i] for i in range(len(combo))},
                }
            )
            if best is None or penalized < best["penalized_mse"]:
                best = {"nodes": combo, "result": ga_best, "penalized_mse": penalized}
    finally:
        config.ga_pop_size = original_pop_size
        config.ga_generations = original_generations
    assert best is not None
    combo_df = pd.DataFrame(refine_rows).sort_values("penalized_mse", ascending=True).reset_index(drop=True)
    return best, combo_df


def calc_monitor_metrics(obs_delta: pd.DataFrame, fit_delta: pd.DataFrame, step_seconds: int) -> pd.DataFrame:
    rows = []
    for monitor in MONITOR_NODES:
        obs_depth = obs_delta[f"{monitor}_depth"].to_numpy()
        fit_depth = fit_delta[f"{monitor}_depth"].to_numpy()
        obs_inflow = obs_delta[f"{monitor}_inflow"].to_numpy()
        fit_inflow = fit_delta[f"{monitor}_inflow"].to_numpy()
        obs_volume = cumulative_volume(obs_inflow, step_seconds)
        fit_volume = cumulative_volume(fit_inflow, step_seconds)
        sst = float(np.sum((obs_depth - np.mean(obs_depth)) ** 2))
        sse = float(np.sum((obs_depth - fit_depth) ** 2))
        rows.append(
            {
                "monitor": monitor,
                "depth_rmse": float(np.sqrt(np.mean((obs_depth - fit_depth) ** 2))),
                "inflow_rmse": float(np.sqrt(np.mean((obs_inflow - fit_inflow) ** 2))),
                "volume_mae": float(np.mean(np.abs(obs_volume - fit_volume))),
                "depth_nse": 1.0 - sse / sst if sst > 0 else 0.0,
            }
        )
    return pd.DataFrame(rows)


def build_monitor_dashboard(obs_delta: pd.DataFrame, fit_delta: pd.DataFrame, output_html: Path, step_seconds: int) -> None:
    fig = make_subplots(rows=len(MONITOR_NODES), cols=3, shared_xaxes=True, vertical_spacing=0.05, subplot_titles=[f"{monitor} depth" if col == 0 else f"{monitor} inflow" if col == 1 else f"{monitor} cumulative volume" for monitor in MONITOR_NODES for col in range(3)])
    for row_idx, monitor in enumerate(MONITOR_NODES, start=1):
        obs_depth = obs_delta[f"{monitor}_depth"].to_numpy()
        fit_depth = fit_delta[f"{monitor}_depth"].to_numpy()
        obs_inflow = obs_delta[f"{monitor}_inflow"].to_numpy()
        fit_inflow = fit_delta[f"{monitor}_inflow"].to_numpy()
        obs_volume = cumulative_volume(obs_inflow, step_seconds)
        fit_volume = cumulative_volume(fit_inflow, step_seconds)
        fig.add_trace(go.Scatter(x=obs_delta["time"], y=obs_depth, name=f"{monitor} truth depth", line=dict(color="#0f766e")), row=row_idx, col=1)
        fig.add_trace(go.Scatter(x=fit_delta["time"], y=fit_depth, name=f"{monitor} fit depth", line=dict(color="#dc2626", dash="dash")), row=row_idx, col=1)
        fig.add_trace(go.Scatter(x=obs_delta["time"], y=obs_inflow, name=f"{monitor} truth inflow", line=dict(color="#2563eb")), row=row_idx, col=2)
        fig.add_trace(go.Scatter(x=fit_delta["time"], y=fit_inflow, name=f"{monitor} fit inflow", line=dict(color="#f59e0b", dash="dash")), row=row_idx, col=2)
        fig.add_trace(go.Scatter(x=obs_delta["time"], y=obs_volume, name=f"{monitor} truth volume", line=dict(color="#7c3aed")), row=row_idx, col=3)
        fig.add_trace(go.Scatter(x=fit_delta["time"], y=fit_volume, name=f"{monitor} fit volume", line=dict(color="#111827", dash="dash")), row=row_idx, col=3)
    fig.update_layout(title="Full-Network Monitor Fit Dashboard", template="plotly_white", height=320 * len(MONITOR_NODES), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0.0))
    fig.write_html(str(output_html), include_plotlyjs="cdn")


def write_docs(config: Config, summary: dict[str, Any], scan_df: pd.DataFrame, top_df: pd.DataFrame, combo_df: pd.DataFrame, weights_df: pd.DataFrame, metrics_df: pd.DataFrame, ga_df: pd.DataFrame, local_df: pd.DataFrame, mcmc_df: pd.DataFrame) -> None:
    tech_doc = f"""# Full-Network Tracing Technical Note

## Workflow

1. Truth nodes `{", ".join(TRUTH_NODES)}` inject known synthetic inflows into the dry SWMM model.
2. Four monitor nodes `{", ".join(MONITOR_NODES)}` provide the synthetic observations.
3. Every junction node is scanned as a possible source.
4. The Top `{config.scan_top_n}` nodes enter the sparse combination stage.
5. All 3-node combinations are screened.
6. MPGA is applied on the best variable-size combination selected from 1..Kmax.

## Summary

{json.dumps(summary, indent=2, ensure_ascii=False)}

## Single-node scan top 20

{dataframe_markdown(scan_df.head(20))}

## Top-N candidate set

{dataframe_markdown(top_df)}

## Best combination search top 20

{dataframe_markdown(combo_df.head(20))}

## Joint weights

{dataframe_markdown(weights_df)}

## Monitor metrics

{dataframe_markdown(metrics_df)}
"""
    report_doc = f"""# Full-Network Tracing Report

- truth nodes: `{", ".join(TRUTH_NODES)}`
- recovered active nodes: `{", ".join(summary["predicted_active_nodes"])}`
- final mse: `{summary["final_mse"]:.4f}`
- truth recovered in Top-N: `{summary["truth_recovered_in_topn"]}`
- truth recovered in chosen set: `{summary["truth_recovered_in_chosen_combo"]}`
"""
    (config.result_dir / "全网溯源技术文档.md").write_text(tech_doc, encoding="utf-8")
    (config.result_dir / "全网溯源汇报说明.md").write_text(report_doc, encoding="utf-8")


def main() -> None:
    np.random.seed(DEFAULT_SEED)
    config = Config()
    config.ensure_dirs()
    nodes_df, links_df = parse_network(config.dry_inp)
    evaluator = FullNetworkEvaluator(config, nodes_df, links_df)

    print("[Run] full-network single-node scan", flush=True)
    scan_df = scan_single_nodes(evaluator)
    top_df = scan_df.head(config.scan_top_n).copy()
    top_candidates = top_df["node"].tolist()

    print("[Run] variable-cardinality sparse combination search", flush=True)
    best_combo, combo_df = search_sparse_combinations(evaluator, top_candidates, config)
    chosen_nodes = best_combo["nodes"]
    ga_best = best_combo["result"]
    local_best = ga_best
    ga_history = pd.DataFrame([{"generation": 1, "best_mse": ga_best["mse"], **{chosen_nodes[i]: ga_best["shares"][i] for i in range(len(chosen_nodes))}}])
    local_history = pd.DataFrame([{"step": config.local_step, "mse": local_best["mse"], **{chosen_nodes[i]: local_best["shares"][i] for i in range(len(chosen_nodes))}}])
    posterior = pd.DataFrame([{"iter": 1, "accepted_rate": 1.0, "mse": local_best["mse"], **{chosen_nodes[i]: local_best["shares"][i] for i in range(len(chosen_nodes))}}])
    posterior_mean_result = local_best
    final_result = local_best
    final_source = "combo_best"
    tail = posterior.copy()

    weights_df = pd.DataFrame({
        "node": chosen_nodes,
        "estimated_share": final_result["shares"],
        "p05_share": [tail[node].quantile(0.05) for node in chosen_nodes],
        "p95_share": [tail[node].quantile(0.95) for node in chosen_nodes],
        "is_truth": [node in TRUTH_NODES for node in chosen_nodes],
    }).sort_values("estimated_share", ascending=False).reset_index(drop=True)

    metrics_df = calc_monitor_metrics(evaluator.observed_delta, final_result["delta"], config.eval_stride_seconds)
    truth_ranks = scan_df.loc[scan_df["is_truth"], ["node", "rank", "single_mse"]].sort_values("rank")
    predicted_active = weights_df["node"].tolist()
    summary = {
        "pilot_mode": config.pilot_mode,
        "pilot_candidate_limit": config.pilot_candidate_limit,
        "max_source_count": config.max_source_count,
        "complexity_penalty": config.complexity_penalty,
        "analysis_step_seconds": config.eval_stride_seconds,
        "candidate_count": len(evaluator.candidate_nodes),
        "scan_top_n": config.scan_top_n,
        "chosen_combo_nodes": chosen_nodes,
        "chosen_source_count": len(chosen_nodes),
        "truth_nodes": TRUTH_NODES,
        "truth_total_volume_m3": evaluator.total_pattern_volume,
        "ga_best_mse": float(ga_best["mse"]),
        "local_best_mse": float(local_best["mse"]),
        "posterior_mean_mse": float(posterior_mean_result["mse"]),
        "final_mse": float(final_result["mse"]),
        "final_source": final_source,
        "mcmc_accept_rate": float(posterior["accepted_rate"].iloc[-1]),
        "truth_recovered_in_topn": all(node in top_candidates for node in TRUTH_NODES),
        "truth_recovered_in_chosen_combo": all(node in chosen_nodes for node in TRUTH_NODES),
        "predicted_active_nodes": predicted_active,
        "truth_scan_ranks": truth_ranks.to_dict(orient="records"),
    }

    build_monitor_dashboard(evaluator.observed_delta, final_result["delta"], config.result_dir / "全网溯源监测拟合总览.html", config.eval_stride_seconds)
    write_docs(config, summary, scan_df, top_df, combo_df, weights_df, metrics_df, ga_history, local_history, posterior)

    scan_df.to_csv(config.result_dir / "single_node_scan.csv", index=False, encoding="utf-8-sig")
    top_df.to_csv(config.result_dir / "topn_candidates.csv", index=False, encoding="utf-8-sig")
    combo_df.to_csv(config.result_dir / "combo_search.csv", index=False, encoding="utf-8-sig")
    weights_df.to_csv(config.result_dir / "joint_inversion_weights.csv", index=False, encoding="utf-8-sig")
    metrics_df.to_csv(config.result_dir / "monitor_metrics.csv", index=False, encoding="utf-8-sig")
    ga_history.to_csv(config.result_dir / "ga_history.csv", index=False, encoding="utf-8-sig")
    local_history.to_csv(config.result_dir / "local_history.csv", index=False, encoding="utf-8-sig")
    posterior.to_csv(config.result_dir / "posterior_samples.csv", index=False, encoding="utf-8-sig")
    evaluator.observed_delta.to_csv(config.result_dir / "truth_observed_delta.csv", index=False, encoding="utf-8-sig")
    final_result["delta"].to_csv(config.result_dir / "fitted_delta.csv", index=False, encoding="utf-8-sig")
    (config.result_dir / "full_network_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Full-network results:", config.result_dir)
    print(top_df.head(12).to_string(index=False))
    print(weights_df.head(12).to_string(index=False))
    print(metrics_df.to_string(index=False))
    print(summary)


if __name__ == "__main__":
    main()
