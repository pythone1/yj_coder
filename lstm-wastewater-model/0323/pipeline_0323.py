from __future__ import annotations

import importlib.util
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


DEFAULT_SEED = 42
RAIN_SERIES_NAME = "21"


def load_base_module():
    module_path = Path(r"E:\PY\LSTM\swmm_case\full_network_source_tracing.py")
    spec = importlib.util.spec_from_file_location("source_tracing_base_0323", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


base = load_base_module()


@dataclass
class Config:
    """0323 主链配置。"""

    work_dir: Path = Path(r"E:\PY\LSTM\0323")
    dry_inp: Path = Path(r"E:\PY\LSTM\0323\case_dry_full.inp")
    result_dir: Path = Path(r"E:\PY\LSTM\0323\results")

    eval_stride_seconds: int = 600
    truth_nodes: tuple[str, ...] = ("J124", "J129")
    monitor_nodes: tuple[str, ...] = ("J226", "J127", "J128", "J130", "J131")
    outlet_node: str = "J226"
    candidate_nodes: tuple[str, ...] = (
        "J126", "J127", "J128", "J227", "J129", "J228", "J125", "J130", "J225", "J229",
        "J124", "J131", "J123", "J133", "J143", "J134", "J135", "J136", "J137", "J138",
    )

    event_start_offset_hours: float = 2.0
    event_duration_hours: float = 8.0
    truth_total_volume_m3: float = 5200.0
    truth_volume_shares: tuple[float, ...] = (0.55, 0.45)

    ga_pop_count: int = 2
    ga_pop_size: int = 6
    ga_generations: int = 4
    ga_migration_interval: int = 2
    elite_ratio: float = 0.25
    mutation_sigma: float = 0.10
    initial_ppd_keep_ratio: float = 0.70

    prior_component_scale: float = 1.20
    am_samples: int = 30
    am_burn_in: int = 8
    adaptive_start: int = 8
    am_chain_count: int = 3
    sigma_obs: float = 0.03
    am_eps: float = 1e-6
    am_scale_override: float | None = None
    posterior_validation_sample_count: int = 16

    tau_floor: float = 0.03
    tau_cap: float = 0.20

    def ensure_dirs(self) -> None:
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.result_dir.mkdir(parents=True, exist_ok=True)


def parse_timeseries_from_inp(inp_path: Path, series_name: str) -> pd.DataFrame:
    section = None
    rows: list[tuple[float, float]] = []
    for raw in inp_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith(";;") or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line.upper()
            continue
        if section != "[TIMESERIES]":
            continue
        parts = line.split()
        if len(parts) < 3 or parts[0] != series_name:
            continue
        rows.append((float(parts[1]), float(parts[2])))
    if not rows:
        raise RuntimeError(f"未在 INP 中找到时序 {series_name}")
    return pd.DataFrame(rows, columns=["minute", "value"]).sort_values("minute").reset_index(drop=True)


def build_rain_driven_shape(sim_times: pd.Series, event_start: pd.Timestamp, duration_hours: float, rain_df: pd.DataFrame) -> np.ndarray:
    event_end = event_start + pd.Timedelta(hours=duration_hours)
    sim_minutes = ((sim_times - sim_times.iloc[0]).dt.total_seconds() / 60.0).to_numpy(dtype=float)
    start_min = float((event_start - sim_times.iloc[0]).total_seconds() / 60.0)
    end_min = float((event_end - sim_times.iloc[0]).total_seconds() / 60.0)
    rain_x = rain_df["minute"].to_numpy(dtype=float)
    rain_y = rain_df["value"].to_numpy(dtype=float)
    rain_x = (rain_x - rain_x.min()) / max(rain_x.max() - rain_x.min(), 1e-8)
    scaled_x = start_min + rain_x * (end_min - start_min)
    shape = np.interp(sim_minutes, scaled_x, rain_y, left=0.0, right=0.0)
    return np.maximum(shape, 0.0)


def project_to_simplex(raw: np.ndarray) -> np.ndarray:
    values = np.maximum(np.asarray(raw, dtype=float), 0.0)
    total = float(values.sum())
    if total <= 1e-12:
        return np.full(len(values), 1.0 / len(values))
    return values / total


def nse(obs: np.ndarray, sim: np.ndarray) -> float:
    denom = float(np.sum((obs - np.mean(obs)) ** 2))
    if denom < 1e-12:
        return 1.0 if np.allclose(obs, sim) else -np.inf
    return 1.0 - float(np.sum((obs - sim) ** 2)) / denom


def build_subnetwork_views(nodes_df: pd.DataFrame, links_df: pd.DataFrame, config: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    chosen = set(config.candidate_nodes) | set(config.monitor_nodes) | set(config.truth_nodes) | {config.outlet_node}
    node_view = nodes_df[nodes_df["node"].isin(chosen)].copy()
    link_view = links_df[links_df["from_node"].isin(chosen) & links_df["to_node"].isin(chosen)].copy()
    return node_view, link_view


class FineDataset:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.nodes_df, self.links_df = base.parse_network(config.dry_inp)
        self.sub_nodes_df, self.sub_links_df = build_subnetwork_views(self.nodes_df, self.links_df, config)
        self.sim_times = base.simulation_times(config.dry_inp, config.eval_stride_seconds)
        self.sim_minutes = ((self.sim_times["time"] - self.sim_times["time"].iloc[0]).dt.total_seconds() / 60.0).to_numpy()
        self.event_start = self.sim_times["time"].iloc[0] + pd.Timedelta(hours=config.event_start_offset_hours)
        self.event_end = self.event_start + pd.Timedelta(hours=config.event_duration_hours)
        self.event_mask = (self.sim_times["time"] >= self.event_start) & (self.sim_times["time"] <= self.event_end)

        rain_df = parse_timeseries_from_inp(config.dry_inp, RAIN_SERIES_NAME)
        raw_shape = build_rain_driven_shape(self.sim_times["time"], self.event_start, config.event_duration_hours, rain_df)
        pattern_volume = float(np.sum(raw_shape) * config.eval_stride_seconds)
        if pattern_volume <= 1e-8:
            raise RuntimeError("降雨驱动时间分配体积过小，无法构造注入。")
        self.normalized_shape = raw_shape / pattern_volume

        truth_shares = project_to_simplex(np.asarray(config.truth_volume_shares, dtype=float))
        self.truth_templates = {
            node: self.normalized_shape * (config.truth_total_volume_m3 * truth_shares[idx])
            for idx, node in enumerate(config.truth_nodes)
        }

        sim_monitor_nodes = list(dict.fromkeys(list(config.monitor_nodes) + [config.outlet_node]))
        self.dry_metrics_full = base.run_dynamic_simulation(str(config.dry_inp), config.eval_stride_seconds, sim_monitor_nodes, None, False, None, None)["metrics"]
        self.truth_metrics_full = base.run_dynamic_simulation(str(config.dry_inp), config.eval_stride_seconds, sim_monitor_nodes, self.truth_templates, False, None, None)["metrics"]
        self.dry_metrics = self.dry_metrics_full.loc[self.event_mask].reset_index(drop=True)
        self.truth_metrics = self.truth_metrics_full.loc[self.event_mask].reset_index(drop=True)
        self.observed_delta = self.make_delta(self.truth_metrics, self.dry_metrics)

        outlet_series = self.observed_delta[f"{config.outlet_node}_inflow"].to_numpy(dtype=float)
        self.q_r = abs(float(np.sum(outlet_series) * config.eval_stride_seconds))
        self.obs_flow = {monitor: self.observed_delta[f"{monitor}_inflow"].to_numpy(dtype=float) for monitor in config.monitor_nodes}

    @staticmethod
    def make_delta(run_df: pd.DataFrame, base_df: pd.DataFrame) -> pd.DataFrame:
        merged = run_df.merge(base_df, on="time", suffixes=("_run", "_base"))
        out = pd.DataFrame({"time": merged["time"]})
        metric_names = sorted({item.replace("_run", "") for item in merged.columns if item.endswith("_run")})
        for name in metric_names:
            out[name] = merged[f"{name}_run"] - merged[f"{name}_base"]
        return out

    def crop_metrics(self, metrics_df: pd.DataFrame) -> pd.DataFrame:
        return metrics_df.loc[self.event_mask].reset_index(drop=True)

    def build_injections(self, shares: np.ndarray) -> dict[str, np.ndarray]:
        shares = project_to_simplex(shares)
        return {node: self.normalized_shape * float(shares[idx] * self.q_r) for idx, node in enumerate(self.config.candidate_nodes)}

class Evaluator:
    def __init__(self, dataset: FineDataset) -> None:
        self.data = dataset
        self.cache: dict[tuple[float, ...], dict[str, object]] = {}

    def evaluate_plan(self, shares: np.ndarray) -> dict[str, object]:
        shares = project_to_simplex(shares)
        key = tuple(np.round(shares, 8))
        if key in self.cache:
            return self.cache[key]

        injections = self.data.build_injections(shares)
        sim_metrics_full = base.run_dynamic_simulation(
            str(self.data.config.dry_inp),
            self.data.config.eval_stride_seconds,
            list(dict.fromkeys(list(self.data.config.monitor_nodes) + [self.data.config.outlet_node])),
            injections,
            False,
            None,
            None,
        )["metrics"]
        sim_metrics = self.data.crop_metrics(sim_metrics_full)
        delta = self.data.make_delta(sim_metrics, self.data.dry_metrics)
        sim_flow = {monitor: delta[f"{monitor}_inflow"].to_numpy(dtype=float) for monitor in self.data.config.monitor_nodes}
        nse_values = [nse(self.data.obs_flow[monitor], sim_flow[monitor]) for monitor in self.data.config.monitor_nodes]
        mean_nse = float(np.mean(nse_values))
        sse = float(sum(np.sum((self.data.obs_flow[m] - sim_flow[m]) ** 2) for m in self.data.config.monitor_nodes))
        result = {"shares": shares, "delta": delta, "mean_nse": mean_nse, "loss": 1.0 - mean_nse, "sse": sse, "nse_values": nse_values}
        self.cache[key] = result
        return result


def seed_population(candidate_nodes: tuple[str, ...], pop_size: int) -> np.ndarray:
    """真正盲测的 GA 初始化。"""
    dim = len(candidate_nodes)
    seeds: list[np.ndarray] = []
    sparse_seed_count = min(4, pop_size)
    for _ in range(sparse_seed_count):
        vec = np.zeros(dim, dtype=float)
        active_count = np.random.randint(1, min(4, dim) + 1)
        active_idx = np.random.choice(dim, size=active_count, replace=False)
        vec[active_idx] = np.random.uniform(0.2, 1.0, size=active_count)
        seeds.append(project_to_simplex(vec))
    while len(seeds) < pop_size:
        seeds.append(np.random.dirichlet(np.ones(dim, dtype=float)))
    return np.array(seeds[:pop_size])


def build_initial_ppd(merged_df: pd.DataFrame, config: Config) -> pd.DataFrame:
    keep_count = max(4, int(len(merged_df) * config.initial_ppd_keep_ratio))
    scored = merged_df.copy()
    fitness = scored["mean_nse"].to_numpy(dtype=float)
    fitness = fitness - np.min(fitness) + 1e-6
    probability = fitness / fitness.sum()
    scored["roulette_probability"] = probability
    chosen_idx = np.random.choice(scored.index.to_numpy(), size=min(keep_count, len(scored)), replace=False, p=probability)
    selected = scored.loc[chosen_idx].copy().sort_values(["mean_nse", "loss"], ascending=[False, True]).reset_index(drop=True)
    selected["ppd_rank"] = np.arange(1, len(selected) + 1)
    return selected


def ga_search(evaluator: Evaluator, config: Config) -> tuple[dict[str, object], pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    dim = len(config.candidate_nodes)
    populations = [seed_population(config.candidate_nodes, config.ga_pop_size)]
    while len(populations) < config.ga_pop_count:
        populations.append(np.random.dirichlet(np.ones(dim), size=config.ga_pop_size))

    elite_count = max(2, int(config.ga_pop_size * config.elite_ratio))
    best = None
    history_rows: list[dict[str, object]] = []
    all_rows: list[dict[str, object]] = []
    last_generation_rows: list[dict[str, object]] = []

    for generation in range(config.ga_generations):
        print(f"[0323 GA] generation {generation + 1}/{config.ga_generations}", flush=True)
        next_populations = []
        generation_rows: list[dict[str, object]] = []
        for pop_idx, population in enumerate(populations, start=1):
            evaluated = [evaluator.evaluate_plan(shares) for shares in population]
            evaluated.sort(key=lambda item: item["loss"])
            for rank, item in enumerate(evaluated, start=1):
                row = {"generation": generation + 1, "population": pop_idx, "population_rank": rank, "loss": float(item["loss"]), "mean_nse": float(item["mean_nse"]), "sse": float(item["sse"])}
                row.update({node: float(item["shares"][idx]) for idx, node in enumerate(config.candidate_nodes)})
                generation_rows.append(row)
                all_rows.append(row)
            if best is None or evaluated[0]["loss"] < best["loss"]:
                best = evaluated[0]
            elites = [item["shares"] for item in evaluated[:elite_count]]
            children = elites.copy()
            while len(children) < config.ga_pop_size:
                pa = elites[np.random.randint(0, len(elites))]
                pb = elites[np.random.randint(0, len(elites))]
                child = project_to_simplex(0.5 * pa + 0.5 * pb + np.random.normal(0.0, config.mutation_sigma, size=dim))
                children.append(child)
            next_populations.append(np.array(children))
        if best is not None and (generation + 1) % config.ga_migration_interval == 0:
            for population in next_populations[1:]:
                population[0] = best["shares"]
        history_rows.append({"generation": generation + 1, "best_loss": float(best["loss"]), "best_mean_nse": float(best["mean_nse"]), **{node: float(best["shares"][idx]) for idx, node in enumerate(config.candidate_nodes)}})
        populations = next_populations
        last_generation_rows = generation_rows

    merged_df = pd.DataFrame(last_generation_rows)
    all_df = pd.DataFrame(all_rows)
    initial_ppd_df = build_initial_ppd(merged_df, config)
    return best, pd.DataFrame(history_rows), merged_df, all_df, initial_ppd_df


def multivariate_logpdf(x: np.ndarray, mean: np.ndarray, cov: np.ndarray) -> float:
    dim = len(x)
    cov = np.asarray(cov, dtype=float) + np.eye(dim) * 1e-9
    sign, logdet = np.linalg.slogdet(cov)
    if sign <= 0:
        cov = cov + np.eye(dim) * 1e-6
        sign, logdet = np.linalg.slogdet(cov)
    inv_cov = np.linalg.inv(cov)
    diff = np.asarray(x, dtype=float) - np.asarray(mean, dtype=float)
    quad = float(diff.T @ inv_cov @ diff)
    return -0.5 * (dim * math.log(2.0 * math.pi) + logdet + quad)


def logsumexp(values: np.ndarray) -> float:
    vmax = float(np.max(values))
    return vmax + math.log(float(np.sum(np.exp(values - vmax))))


def build_prior_model(initial_ppd_df: pd.DataFrame, node_names: tuple[str, ...], config: Config) -> dict[str, object]:
    samples = initial_ppd_df[list(node_names)].to_numpy(dtype=float)
    weights = initial_ppd_df["roulette_probability"].to_numpy(dtype=float)
    weights = weights / weights.sum()
    if len(samples) >= 2:
        sample_cov = np.cov(samples.T) + np.eye(len(node_names)) * 1e-6
    else:
        sample_cov = np.eye(len(node_names)) * (config.sigma_obs ** 2)
    component_cov = sample_cov * config.prior_component_scale + np.eye(len(node_names)) * 1e-6
    return {"samples": samples, "weights": weights, "component_cov": component_cov}


def prior_logpdf(x: np.ndarray, prior_model: dict[str, object]) -> float:
    samples = np.asarray(prior_model["samples"], dtype=float)
    weights = np.asarray(prior_model["weights"], dtype=float)
    component_cov = np.asarray(prior_model["component_cov"], dtype=float)
    logs = np.array([math.log(max(w, 1e-12)) + multivariate_logpdf(x, mu, component_cov) for mu, w in zip(samples, weights)], dtype=float)
    return logsumexp(logs)


def adaptive_covariance(history: np.ndarray, dim: int, eps: float, scale: float) -> np.ndarray:
    if len(history) < 2:
        return np.eye(dim) * (scale * eps)
    cov = np.cov(history.T)
    cov = np.asarray(cov, dtype=float)
    if cov.ndim == 0:
        cov = np.eye(dim) * float(cov)
    return scale * cov + scale * eps * np.eye(dim)


def am_sampling(evaluator: Evaluator, initial_ppd_df: pd.DataFrame, config: Config, chain_id: int) -> pd.DataFrame:
    np.random.seed(DEFAULT_SEED + chain_id)
    node_names = config.candidate_nodes
    dim = len(node_names)
    sd = config.am_scale_override if config.am_scale_override is not None else (2.42 / dim)
    prior_model = build_prior_model(initial_ppd_df, node_names, config)
    prior_cov = np.asarray(prior_model["component_cov"], dtype=float)

    start_rank = min(chain_id - 1, len(initial_ppd_df) - 1)
    current_shares = project_to_simplex(initial_ppd_df.iloc[start_rank][list(node_names)].to_numpy(dtype=float))
    current = evaluator.evaluate_plan(current_shares)
    current_log_like = -current["sse"] / (2.0 * config.sigma_obs ** 2)
    current_log_prior = prior_logpdf(current_shares, prior_model)
    current_log_post = current_log_like + current_log_prior
    base_cov = sd * prior_cov + sd * config.am_eps * np.eye(dim)

    accepted = 0
    rows = []
    for step in range(config.am_samples):
        cov = base_cov if step < config.adaptive_start or len(rows) < 2 else adaptive_covariance(np.array([[row[node] for node in node_names] for row in rows], dtype=float), dim, config.am_eps, sd)
        proposal = np.random.multivariate_normal(current_shares, cov)
        proposal = project_to_simplex(proposal)
        candidate = evaluator.evaluate_plan(proposal)
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
        row = {"chain": chain_id, "iteration": step + 1, "accepted_rate": accepted / (step + 1), "log_like": current_log_like, "log_prior": current_log_prior, "log_posterior": current_log_post, "proposal_scale_sd": sd, "cov_trace": float(np.trace(cov))}
        row.update({node: float(current_shares[idx]) for idx, node in enumerate(node_names)})
        rows.append(row)
    return pd.DataFrame(rows)

def dynamic_tau(mean_shares: pd.Series, config: Config) -> float:
    sorted_values = np.sort(mean_shares.to_numpy())[::-1]
    if len(sorted_values) < 2:
        return config.tau_floor
    gaps = sorted_values[:-1] - sorted_values[1:]
    idx = int(np.argmax(gaps))
    tau = float((sorted_values[idx] + sorted_values[idx + 1]) / 2.0)
    return float(np.clip(tau, config.tau_floor, config.tau_cap))


def build_weights(tail_df: pd.DataFrame, config: Config) -> pd.DataFrame:
    mean_shares = pd.Series({node: float(tail_df[node].mean()) for node in config.candidate_nodes}, dtype=float)
    tau = dynamic_tau(mean_shares, config)
    weights = pd.DataFrame({
        "node": list(config.candidate_nodes),
        "posterior_mean_share": [mean_shares[node] for node in config.candidate_nodes],
        "posterior_median_share": [float(tail_df[node].median()) for node in config.candidate_nodes],
        "p05_share": [float(tail_df[node].quantile(0.05)) for node in config.candidate_nodes],
        "p95_share": [float(tail_df[node].quantile(0.95)) for node in config.candidate_nodes],
        "is_truth": [node in config.truth_nodes for node in config.candidate_nodes],
    }).sort_values("posterior_mean_share", ascending=False).reset_index(drop=True)
    weights["is_active"] = weights["posterior_mean_share"] >= tau
    weights["tau"] = tau
    return weights


def choose_final_solution(evaluator: Evaluator, ga_best: dict[str, object], initial_ppd_df: pd.DataFrame, posterior_df: pd.DataFrame, tail_df: pd.DataFrame, config: Config) -> tuple[dict[str, object], pd.Series]:
    node_names = list(config.candidate_nodes)
    mean_series = pd.Series({node: float(tail_df[node].mean()) for node in node_names}, dtype=float)
    median_series = pd.Series({node: float(tail_df[node].median()) for node in node_names}, dtype=float)
    best_idx = int(posterior_df["log_posterior"].idxmax())
    posterior_best = pd.Series({node: float(posterior_df.loc[best_idx, node]) for node in node_names}, dtype=float)
    initial_mean = pd.Series({node: float(initial_ppd_df[node].mean()) for node in node_names}, dtype=float)
    candidates = [("ga_best", pd.Series(ga_best["shares"], index=node_names, dtype=float)), ("initial_ppd_mean", initial_mean), ("posterior_mean", mean_series), ("posterior_median", median_series), ("posterior_best", posterior_best)]

    best_name = ""
    best_result = None
    best_series = None
    for name, series in candidates:
        shares = project_to_simplex(series.to_numpy(dtype=float))
        result = evaluator.evaluate_plan(shares)
        if best_result is None or result["mean_nse"] > best_result["mean_nse"]:
            best_name = name
            best_result = result
            best_series = pd.Series(shares, index=node_names, dtype=float)
    assert best_result is not None and best_series is not None
    best_result["solution_name"] = best_name
    return best_result, best_series


def classification_metrics(config: Config, predicted_nodes: set[str]) -> dict[str, float]:
    truth_nodes = set(config.truth_nodes)
    candidate_nodes = list(config.candidate_nodes)
    tp = sum(1 for node in candidate_nodes if node in truth_nodes and node in predicted_nodes)
    tn = sum(1 for node in candidate_nodes if node not in truth_nodes and node not in predicted_nodes)
    fp = sum(1 for node in candidate_nodes if node not in truth_nodes and node in predicted_nodes)
    fn = sum(1 for node in candidate_nodes if node in truth_nodes and node not in predicted_nodes)
    total = max(len(candidate_nodes), 1)
    acc = (tp + tn) / total
    denom = math.sqrt(max((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn), 1e-12))
    mcc = ((tp * tn) - (fp * fn)) / denom if denom > 0 else 0.0
    return {"tp": tp, "tn": tn, "fp": fp, "fn": fn, "acc": acc, "mcc": mcc}


def posterior_predictive_validation(evaluator: Evaluator, tail_df: pd.DataFrame, config: Config, sample_count: int = 10) -> tuple[pd.DataFrame, pd.DataFrame]:
    pick_idx = np.linspace(0, len(tail_df) - 1, min(sample_count, len(tail_df)), dtype=int)
    simulations = []
    for idx in pick_idx:
        shares = tail_df.iloc[idx][list(config.candidate_nodes)].to_numpy(dtype=float)
        result = evaluator.evaluate_plan(shares)
        sim_df = result["delta"].copy()
        sim_df["sample_id"] = int(idx)
        simulations.append(sim_df)
    sim_stack = pd.concat(simulations, ignore_index=True)
    band_rows = []
    coverage_rows = []
    for monitor in config.monitor_nodes:
        col = f"{monitor}_inflow"
        per_monitor_rows = []
        for time_value, group in sim_stack.groupby("time"):
            values = group[col].to_numpy(dtype=float)
            obs = float(evaluator.data.observed_delta.loc[evaluator.data.observed_delta["time"] == time_value, col].iloc[0])
            row = {"monitor": monitor, "time": time_value, "observed": obs, "p05": float(np.quantile(values, 0.05)), "p50": float(np.quantile(values, 0.50)), "p95": float(np.quantile(values, 0.95))}
            row["covered_90"] = row["p05"] <= obs <= row["p95"]
            band_rows.append(row)
            per_monitor_rows.append(row)
        coverage_rows.append({"monitor": monitor, "coverage_90": float(np.mean([row["covered_90"] for row in per_monitor_rows]))})
    return pd.DataFrame(band_rows), pd.DataFrame(coverage_rows)


def build_monitor_fit_html(observed_delta: pd.DataFrame, fitted_delta: pd.DataFrame, config: Config, output_html: Path) -> None:
    fig = make_subplots(rows=len(config.monitor_nodes), cols=1, shared_xaxes=True, vertical_spacing=0.03, subplot_titles=[f"{monitor} 监测点流量增量对比" for monitor in config.monitor_nodes])
    for idx, monitor in enumerate(config.monitor_nodes, start=1):
        fig.add_trace(go.Scatter(x=observed_delta["time"], y=observed_delta[f"{monitor}_inflow"], name=f"{monitor} 真实观测", line=dict(color="#ea580c", width=2)), row=idx, col=1)
        fig.add_trace(go.Scatter(x=fitted_delta["time"], y=fitted_delta[f"{monitor}_inflow"], name=f"{monitor} 模型拟合", line=dict(color="#16a34a", width=2, dash="dash")), row=idx, col=1)
    fig.update_layout(title="5 个监测点流量增量拟合图（仅 8 小时事件窗口）", template="plotly_white", height=280 * len(config.monitor_nodes), legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0))
    fig.write_html(str(output_html), include_plotlyjs="cdn")


def build_posterior_predictive_html(bands_df: pd.DataFrame, coverage_df: pd.DataFrame, config: Config, output_html: Path) -> None:
    fig = make_subplots(rows=len(config.monitor_nodes), cols=1, shared_xaxes=True, vertical_spacing=0.03, subplot_titles=[f"{monitor} 后验预测区间（90%覆盖率={coverage_df.loc[coverage_df['monitor'] == monitor, 'coverage_90'].iloc[0]:.2f}）" for monitor in config.monitor_nodes])
    for idx, monitor in enumerate(config.monitor_nodes, start=1):
        df = bands_df[bands_df["monitor"] == monitor].copy()
        fig.add_trace(go.Scatter(x=df["time"], y=df["p95"], line=dict(color="rgba(34,197,94,0)"), showlegend=False, hoverinfo="skip"), row=idx, col=1)
        fig.add_trace(go.Scatter(x=df["time"], y=df["p05"], fill="tonexty", fillcolor="rgba(34,197,94,0.20)", line=dict(color="rgba(34,197,94,0)"), name="90% 后验区间" if idx == 1 else None), row=idx, col=1)
        fig.add_trace(go.Scatter(x=df["time"], y=df["p50"], line=dict(color="#16a34a", width=2), name="后验中位预测" if idx == 1 else None), row=idx, col=1)
        fig.add_trace(go.Scatter(x=df["time"], y=df["observed"], line=dict(color="#ea580c", width=2), name="真实观测" if idx == 1 else None), row=idx, col=1)
    fig.update_layout(title="Posterior Predictive Validation（8 小时事件窗口）", template="plotly_white", height=280 * len(config.monitor_nodes), legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0))
    fig.write_html(str(output_html), include_plotlyjs="cdn")

def build_subnetwork_html(dataset: FineDataset, summary: dict[str, object], output_html: Path) -> None:
    truth_nodes = set(dataset.config.truth_nodes)
    monitor_nodes = set(dataset.config.monitor_nodes)
    predicted_nodes = set(summary["predicted_nodes"])
    candidate_nodes = set(dataset.config.candidate_nodes)
    fig = go.Figure()
    for row in dataset.sub_links_df.itertuples():
        fig.add_trace(go.Scatter(x=[row.x1, row.x2], y=[row.y1, row.y2], mode="lines", line=dict(color="#CBD5E1", width=2), hoverinfo="text", text=f"{row.from_node} -> {row.to_node}", showlegend=False))

    def add_group(group_nodes: list[str], name: str, color: str, symbol: str, size: int) -> None:
        if not group_nodes:
            return
        view = dataset.sub_nodes_df[dataset.sub_nodes_df["node"].isin(group_nodes)]
        fig.add_trace(go.Scatter(x=view["x"], y=view["y"], mode="markers+text", text=view["node"], textposition="top center", name=name, marker=dict(color=color, size=size, symbol=symbol, line=dict(color="white", width=1.2)), hovertemplate="%{text}<extra>" + name + "</extra>"))

    overlap = sorted(truth_nodes & predicted_nodes)
    truth_only = sorted(truth_nodes - predicted_nodes)
    predicted_only = sorted(predicted_nodes - truth_nodes)
    candidate_only = sorted(candidate_nodes - truth_nodes - predicted_nodes - monitor_nodes)
    add_group(sorted(monitor_nodes), "监测点", "#2563EB", "square", 12)
    add_group(overlap, "真值且识别到", "#F59E0B", "diamond", 14)
    add_group(truth_only, "真值但未识别", "#DC2626", "circle", 13)
    add_group(predicted_only, "识别到但非真值", "#16A34A", "star", 16)
    add_group(candidate_only, "其他候选点", "#94A3B8", "circle-open", 10)
    fig.update_layout(title="0323 精细子网络：20 节点研究区与真值/识别结果对比", template="plotly_white", width=1100, height=760, legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0), annotations=[dict(x=1.0, y=1.0, xref="paper", yref="paper", xanchor="right", yanchor="top", showarrow=False, align="left", bordercolor="#CBD5E1", borderwidth=1, bgcolor="rgba(255,255,255,0.95)", text=(f"注入点: {', '.join(dataset.config.truth_nodes)}<br>" f"监测点: {', '.join(dataset.config.monitor_nodes)}<br>" f"子系统唯一汇出端: {dataset.config.outlet_node}<br>" f"Q_R(汇出端积分): {summary['q_r_outlet_based']:.2f} m³<br>" f"事件窗: {summary['event_start']} ~ {summary['event_end']}<br>" f"最终识别: {', '.join(summary['predicted_nodes']) or '无'}"))])
    fig.write_html(str(output_html), include_plotlyjs="cdn")


def write_report(config: Config, summary: dict[str, object], weights_df: pd.DataFrame, coverage_df: pd.DataFrame) -> None:
    text = f"""# 0323 精细数据链路汇报

## 1. 场景设定

- 研究目录：`{config.work_dir}`
- 基础模型：`{config.dry_inp.name}`
- 研究子网络规模：`{len(config.candidate_nodes)}` 个候选节点
- 真实注入点：`{', '.join(config.truth_nodes)}`
- 监测点：`{', '.join(config.monitor_nodes)}`
- 子系统唯一汇出端：`{config.outlet_node}`
- 监测分辨率：`{config.eval_stride_seconds // 60}` 分钟
- 事件窗口：`{summary['event_start']}` 到 `{summary['event_end']}`

## 2. 数据构造

1. 用 dry 模型跑完整基线；
2. 从 INP 中读取降雨时序 `{RAIN_SERIES_NAME}`，把它拉伸到 8 小时事件窗；
3. 在真值节点 `{', '.join(config.truth_nodes)}` 上按该降雨时序分配注入；
4. 把干/湿两组结果都裁剪到事件窗口；
5. 仅对子系统唯一汇出端 `{config.outlet_node}` 的流量增量积分，得到：

`Q_R = {summary['q_r_outlet_based']:.2f} m³`

## 3. 算法主链

### 3.1 多种群 GA

- 种群数：`{config.ga_pop_count}`
- 每群个体数：`{config.ga_pop_size}`
- 进化代数：`{config.ga_generations}`
- 目标函数：5 个监测点流量增量序列的平均 `NSE`
- 初始化方式：完全盲测，只使用随机稀疏 seed 与 Dirichlet 样本

### 3.2 AM

- 样本数：`{config.am_samples}`
- burn-in：`{config.am_burn_in}`
- adaptive start：`{config.adaptive_start}`
- posterior = prior + likelihood

## 4. 当前结果

- 最终解来源：`{summary['final_solution_name']}`
- 最终 Mean NSE：`{summary['final_mean_nse']:.4f}`
- 当前识别节点：`{', '.join(summary['predicted_nodes']) or '无'}`
- 真值节点：`{', '.join(summary['truth_nodes'])}`
- ACC：`{summary['acc']:.4f}`
- MCC：`{summary['mcc']:.4f}`
- Posterior 90%覆盖均值：`{summary['posterior_coverage_mean']:.4f}`

## 5. Posterior Predictive 验证

{coverage_df.to_string(index=False)}

## 6. 节点后验结果

{weights_df.to_string(index=False)}
"""
    (config.result_dir / "0323_汇报说明.md").write_text(text, encoding="utf-8")


def run_pipeline(config: Config | None = None) -> dict[str, object]:
    if config is None:
        config = Config()
    np.random.seed(DEFAULT_SEED)
    config.ensure_dirs()
    dataset = FineDataset(config)
    evaluator = Evaluator(dataset)
    ga_best, ga_history_df, merged_last_df, ga_population_df, initial_ppd_df = ga_search(evaluator, config)
    posterior_chains = [am_sampling(evaluator, initial_ppd_df, config, chain_id) for chain_id in range(1, config.am_chain_count + 1)]
    posterior_df = pd.concat(posterior_chains, ignore_index=True)
    tail_df = pd.concat([chain.iloc[config.am_burn_in :].copy() for chain in posterior_chains], ignore_index=True)
    final_result, final_series = choose_final_solution(evaluator, ga_best, initial_ppd_df, posterior_df, tail_df, config)
    weights_df = build_weights(tail_df, config)
    weights_df["final_share"] = weights_df["node"].map(final_series.to_dict())
    weights_df["final_is_active"] = weights_df["final_share"] >= float(weights_df["tau"].iloc[0])
    predicted_nodes = sorted(weights_df.loc[weights_df["final_is_active"], "node"].tolist())
    metrics = classification_metrics(config, set(predicted_nodes))
    truth_share_map = {node: share for node, share in zip(config.truth_nodes, project_to_simplex(np.asarray(config.truth_volume_shares, dtype=float)))}
    pred_share_map = final_series.to_dict()
    mae_all = float(np.mean([abs(pred_share_map.get(node, 0.0) - truth_share_map.get(node, 0.0)) for node in config.candidate_nodes]))
    mae_truth = float(np.mean([abs(pred_share_map.get(node, 0.0) - truth_share_map.get(node, 0.0)) for node in config.truth_nodes]))
    bands_df, coverage_df = posterior_predictive_validation(evaluator, tail_df, config, sample_count=config.posterior_validation_sample_count)
    summary = {
        "candidate_count": len(config.candidate_nodes),
        "candidate_nodes": list(config.candidate_nodes),
        "truth_nodes": list(config.truth_nodes),
        "monitor_nodes": list(config.monitor_nodes),
        "outlet_node": config.outlet_node,
        "predicted_nodes": predicted_nodes,
        "analysis_step_seconds": config.eval_stride_seconds,
        "event_start": str(dataset.event_start),
        "event_end": str(dataset.event_end),
        "merged_last_generation_size": int(len(merged_last_df)),
        "initial_ppd_size": int(len(initial_ppd_df)),
        "final_mean_nse": float(final_result["mean_nse"]),
        "final_sse": float(final_result["sse"]),
        "final_solution_name": final_result["solution_name"],
        "q_r_outlet_based": float(dataset.q_r),
        "q_r_monitor_based": float(dataset.q_r),
        "tau": float(weights_df["tau"].iloc[0]),
        "acc": float(metrics["acc"]),
        "mcc": float(metrics["mcc"]),
        "mae_all_nodes": mae_all,
        "mae_truth_nodes": mae_truth,
        "am_accept_rate_mean": float(np.mean([chain["accepted_rate"].iloc[-1] for chain in posterior_chains])),
        "am_accept_rate_min": float(np.min([chain["accepted_rate"].iloc[-1] for chain in posterior_chains])),
        "am_accept_rate_max": float(np.max([chain["accepted_rate"].iloc[-1] for chain in posterior_chains])),
        "proposal_scale_sd": float(posterior_chains[0]["proposal_scale_sd"].iloc[-1]),
        "final_cov_trace_mean": float(np.mean([chain["cov_trace"].iloc[-1] for chain in posterior_chains])),
        "am_chain_count": int(config.am_chain_count),
        "posterior_validation_sample_count": int(config.posterior_validation_sample_count),
        "posterior_coverage_mean": float(coverage_df["coverage_90"].mean()),
        "posterior_coverage_min": float(coverage_df["coverage_90"].min()),
        "posterior_coverage_max": float(coverage_df["coverage_90"].max()),
    }
    (config.result_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    dataset.sub_nodes_df.to_csv(config.result_dir / "selected_nodes.csv", index=False, encoding="utf-8-sig")
    dataset.sub_links_df.to_csv(config.result_dir / "selected_links.csv", index=False, encoding="utf-8-sig")
    dataset.dry_metrics.to_csv(config.result_dir / "dry_metrics_10min.csv", index=False, encoding="utf-8-sig")
    dataset.truth_metrics.to_csv(config.result_dir / "truth_metrics_10min.csv", index=False, encoding="utf-8-sig")
    dataset.observed_delta.to_csv(config.result_dir / "observed_delta_10min.csv", index=False, encoding="utf-8-sig")
    ga_history_df.to_csv(config.result_dir / "ga_history.csv", index=False, encoding="utf-8-sig")
    ga_population_df.to_csv(config.result_dir / "ga_population_all.csv", index=False, encoding="utf-8-sig")
    merged_last_df.to_csv(config.result_dir / "ga_merged_last_generation.csv", index=False, encoding="utf-8-sig")
    initial_ppd_df.to_csv(config.result_dir / "initial_ppd.csv", index=False, encoding="utf-8-sig")
    posterior_df.to_csv(config.result_dir / "am_samples.csv", index=False, encoding="utf-8-sig")
    weights_df.to_csv(config.result_dir / "posterior_weights.csv", index=False, encoding="utf-8-sig")
    final_result["delta"].to_csv(config.result_dir / "fitted_delta_10min.csv", index=False, encoding="utf-8-sig")
    bands_df.to_csv(config.result_dir / "posterior_predictive_bands.csv", index=False, encoding="utf-8-sig")
    coverage_df.to_csv(config.result_dir / "posterior_predictive_coverage.csv", index=False, encoding="utf-8-sig")
    build_monitor_fit_html(dataset.observed_delta, final_result["delta"], config, config.result_dir / "monitor_fit_10min.html")
    build_posterior_predictive_html(bands_df, coverage_df, config, config.result_dir / "posterior_predictive_validation.html")
    build_subnetwork_html(dataset, summary, config.result_dir / "selected_subnetwork_overview.html")
    write_report(config, summary, weights_df, coverage_df)
    print("=== 0323 盲测主链完成 ===")
    print("真实注入点:", ", ".join(config.truth_nodes))
    print("监测点:", ", ".join(config.monitor_nodes))
    print("唯一排口:", config.outlet_node)
    print("事件窗口:", dataset.event_start, "->", dataset.event_end)
    print("Q_R(排口积分):", round(summary["q_r_outlet_based"], 2), "m3")
    print("最终识别:", ", ".join(summary["predicted_nodes"]) or "无")
    print("Mean NSE:", round(summary["final_mean_nse"], 4))
    print("ACC:", round(summary["acc"], 4), "MCC:", round(summary["mcc"], 4))
    print("Posterior 90%覆盖均值:", round(summary["posterior_coverage_mean"], 4))
    print("结果目录:", config.result_dir)
    return summary


if __name__ == "__main__":
    run_pipeline()

