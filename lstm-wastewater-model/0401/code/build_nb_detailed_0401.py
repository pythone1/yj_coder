from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent


ROOT = Path(r"E:\PY\LSTM\0401")
NOTEBOOK = ROOT / "notebooks" / "0401_项目全流程拆解_详细版.ipynb"


def md(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line if line.endswith("\n") else line + "\n" for line in text.splitlines()],
    }


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line if line.endswith("\n") else line + "\n" for line in text.splitlines()],
    }


def source_view_cell(path: Path) -> dict:
    return code(
        dedent(
            f"""
            from pathlib import Path

            src_path = Path(r"{path}")
            print("源码文件:", src_path)
            print("-" * 100)
            print(src_path.read_text(encoding="utf-8"))
            """
        ).strip()
    )


def function_source_cell(path: Path, func_name: str) -> dict:
    return code(
        dedent(
            f"""
            from pathlib import Path
            import re

            src_path = Path(r"{path}")
            text = src_path.read_text(encoding="utf-8")
            pattern = re.compile(r"^def {func_name}\\(.*?(?=^def |\\Z)", re.S | re.M)
            match = pattern.search(text)
            if not match:
                raise ValueError("Function not found: {func_name}")
            print(match.group(0))
            """
        ).strip()
    )


def build_notebook() -> dict:
    model_dir = ROOT / "models" / "current_confirmed_models"
    code_dir = ROOT / "code"

    setup_code = dedent(
        r"""
        from __future__ import annotations

        import json
        import shutil
        from dataclasses import dataclass
        from pathlib import Path

        import numpy as np
        import pandas as pd
        import plotly.graph_objects as go
        import plotly.io as pio
        from plotly.subplots import make_subplots
        from pyswmm import Links, Nodes, Simulation

        pio.renderers.default = "notebook_connected"

        ROOT = Path(r"E:\PY\LSTM\0401")
        MODEL_DIR = ROOT / "models" / "current_confirmed_models"
        DATA_DIR = ROOT / "data" / "generated"
        RESULT_SMALL = ROOT / "results" / "small_run"
        RESULT_MEDIUM = ROOT / "results" / "medium_run"
        RUNTIME_DIR = ROOT / "runtime_ascii" / "notebook"
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

        BASELINE_MODEL_INP = next(MODEL_DIR.glob("*基线模型*0.5开0.2关.inp"))
        TRUTH_EVENT_MODEL_INP = next(MODEL_DIR.glob("*0.3倍.inp"))
        LAYOUT_NODE_CSV = MODEL_DIR / "0401_布设方案节点表.csv"
        LAYOUT_LINK_CSV = MODEL_DIR / "0401_布设方案连接表.csv"

        TOTAL_PROCESS_CSV = DATA_DIR / "0401_总入流过程_10分钟.csv"
        TRUTH_INJECTION_CSV = DATA_DIR / "0401_真值注水数据_10分钟.csv"
        BASELINE_MONITOR_CSV = DATA_DIR / "0401_基线监测_10分钟.csv"
        EVENT_MONITOR_CSV = DATA_DIR / "0401_事件监测_10分钟.csv"
        OBSERVED_DELTA_CSV = DATA_DIR / "0401_观测增量_10分钟.csv"
        OUTLET_SERIES_CSV = DATA_DIR / "0401_排口过程_10分钟.csv"

        CANDIDATE_NODES = (
            "J193","J70","J71","J74","J76","J78","J81","J85","J89","J41",
            "J120","J124","J125","J129","J131","J135","J137","J140","J145","J67",
        )
        MONITOR_NODES = ("J74","J77","J78","J123","J126","J141","J139","J145","J231")
        TRUTH_INJECTION_NODES = ("J76","J124","J140")
        OUTFALL_NODE = "J132"
        STEP_MINUTES = 10
        STEP_SECONDS = STEP_MINUTES * 60

        @dataclass(frozen=True)
        class ExperimentConfig:
            ga_population_count: int = 2
            ga_population_size: int = 8
            ga_generations: int = 4
            ga_elite_ratio: float = 0.25
            ga_mutation_strength: float = 0.18
            ga_migration_interval: int = 2
            ga_migration_count: int = 2
            ga_competition_replace_count: int = 2
            am_chain_count: int = 2
            am_samples_per_chain: int = 60
            am_warmup: int = 15
            am_adapt_start: int = 15
            am_initial_covariance: float = 0.002
            am_eps: float = 1e-8
            posterior_validation_samples: int = 12
            parallel_workers: int = 4
            random_seed: int = 20260401
            progress_step_interval: int = 10

        print("基线模板:", BASELINE_MODEL_INP)
        print("事件模板:", TRUTH_EVENT_MODEL_INP)
        print("候选井数量:", len(CANDIDATE_NODES))
        print("监测点数量:", len(MONITOR_NODES))
        print("真值注水点数量:", len(TRUTH_INJECTION_NODES))
        """
    ).strip()

    truth_eval_code = dedent(
        r"""
        def find_outfall_link_name(inp_path: Path, outfall_node: str = OUTFALL_NODE) -> str:
            current_section = ""
            for raw in inp_path.read_text(encoding="gbk", errors="ignore").splitlines():
                s = raw.strip()
                if s.startswith("[") and s.endswith("]"):
                    current_section = s[1:-1].upper()
                    continue
                if current_section != "CONDUITS" or not s or s.startswith(";"):
                    continue
                parts = s.split()
                if len(parts) >= 3 and parts[2] == outfall_node:
                    return parts[0]
            raise ValueError(f"Unable to find conduit flowing into {outfall_node}")

        def extract_truth_injection_from_event_inp(event_inp: Path = TRUTH_EVENT_MODEL_INP) -> pd.DataFrame:
            text = event_inp.read_text(encoding="gbk", errors="ignore")
    wanted = {f"TS_{node}_0327": node for node in TRUTH_INJECTION_NODES}
            rows = {"step": [], "relative_hour": []}
            for node in TRUTH_INJECTION_NODES:
                rows[f"{node}_flow_cms"] = []
            temp = {node: [] for node in TRUTH_INJECTION_NODES}
            times = []
            in_ts = False
            for raw in text.splitlines():
                s = raw.strip()
                if s.startswith("[") and s.endswith("]"):
                    in_ts = s[1:-1].upper() == "TIMESERIES"
                    continue
                if not in_ts or not s or s.startswith(";"):
                    continue
                parts = s.split()
                if len(parts) < 3 or parts[0] not in wanted:
                    continue
                hh, mm = parts[1].split(":")
                rel_hour = int(hh) + int(mm) / 60.0
                node = wanted[parts[0]]
                if node == TRUTH_INJECTION_NODES[0]:
                    times.append(rel_hour)
                temp[node].append(float(parts[2]))
            for idx, rel_hour in enumerate(times):
                rows["step"].append(idx)
                rows["relative_hour"].append(rel_hour)
                for node in TRUTH_INJECTION_NODES:
                    rows[f"{node}_flow_cms"].append(temp[node][idx])
            df = pd.DataFrame(rows)
            for node in TRUTH_INJECTION_NODES:
                df[f"{node}_volume_m3"] = df[f"{node}_flow_cms"] * STEP_SECONDS
            return df

        @dataclass
        class ExperimentDataset:
            total_process: pd.DataFrame
            truth_injection: pd.DataFrame
            baseline_monitor: pd.DataFrame
            event_monitor: pd.DataFrame
            observed_delta: pd.DataFrame
            outlet: pd.DataFrame
            qr_m3: float

        def build_dataset(generated_data: dict[str, pd.DataFrame]) -> ExperimentDataset:
            total_process = generated_data["total_process"].copy()
            return ExperimentDataset(
                total_process=total_process,
                truth_injection=generated_data["truth_injection"].copy(),
                baseline_monitor=generated_data["baseline_monitor"].copy(),
                event_monitor=generated_data["event_monitor"].copy(),
                observed_delta=generated_data["observed_delta"].copy(),
                outlet=generated_data["outlet"].copy(),
                qr_m3=float(total_process["total_volume_m3"].sum()),
            )

        def simplex_project(vector: np.ndarray) -> np.ndarray:
            x = np.asarray(vector, dtype=float).copy()
            x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
            if np.all(x <= 0):
                return np.ones_like(x) / len(x)
            sorted_x = np.sort(x)[::-1]
            cssv = np.cumsum(sorted_x) - 1
            idx = np.arange(1, len(x) + 1)
            cond = sorted_x - cssv / idx > 0
            rho = idx[cond][-1]
            theta = cssv[cond][-1] / rho
            projected = np.maximum(x - theta, 0)
            total = projected.sum()
            if total <= 0:
                return np.ones_like(x) / len(x)
            return projected / total

        def shares_to_inflow_series(shares: np.ndarray, total_process: pd.DataFrame) -> dict[str, np.ndarray]:
            weights = simplex_project(shares)
            total_cms = total_process["total_flow_cms"].to_numpy(dtype=float)
            return {node: total_cms * weights[idx] for idx, node in enumerate(CANDIDATE_NODES)}

        def _format_time_label(relative_hour: float) -> str:
            total_minutes = int(round(relative_hour * 60.0))
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours:02d}:{minutes:02d}"

        def runtime_model_path(worker_id: int = 0) -> Path:
            worker_dir = RUNTIME_DIR / f"worker_{worker_id}"
            worker_dir.mkdir(parents=True, exist_ok=True)
            target = worker_dir / "model.inp"
            shutil.copyfile(BASELINE_MODEL_INP, target)
            return target

        def inject_timeseries_into_inp(runtime_inp: Path, injection_series: dict[str, np.ndarray], total_process: pd.DataFrame) -> None:
            lines = runtime_inp.read_text(encoding="gbk", errors="ignore").splitlines()
            time_labels = [_format_time_label(v) for v in total_process["relative_hour"].to_numpy(dtype=float)]
            ts_names = {node: f"TS_{node}_SIM" for node in injection_series}
            section = ""
            inflow_payload = []
            timeseries_payload = []
            for node_name, series in injection_series.items():
                if np.allclose(series, 0.0):
                    continue
                ts_name = ts_names[node_name]
                inflow_payload.append(f"{node_name:<16} FLOW             {ts_name:<16} FLOW     1.0      1.0      0.0")
                for label, value in zip(time_labels, series):
                    timeseries_payload.append(f"{ts_name:<24} {label:<10} {float(value):.12f}")
            output_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("[") and stripped.endswith("]"):
                    section = stripped[1:-1].upper()
                    output_lines.append(line)
                    continue
                if section == "INFLOWS" and stripped and not stripped.startswith(";"):
                    parts = stripped.split()
                    if len(parts) >= 3 and parts[2].startswith("TS_") and parts[2].endswith("_SIM"):
                        continue
                if section == "TIMESERIES" and stripped and not stripped.startswith(";"):
                    parts = stripped.split()
                    if parts and parts[0].startswith("TS_") and parts[0].endswith("_SIM"):
                        continue
                output_lines.append(line)
                if section == "INFLOWS" and stripped.startswith(";;--------------") and inflow_payload:
                    output_lines.extend(inflow_payload)
                    inflow_payload = []
                if section == "TIMESERIES" and stripped.startswith(";;--------------") and timeseries_payload:
                    output_lines.extend(timeseries_payload)
                    timeseries_payload = []
            runtime_inp.write_text("\n".join(output_lines) + "\n", encoding="gbk")

        def run_event_simulation(runtime_inp: Path, injection_series: dict[str, np.ndarray], total_process: pd.DataFrame):
            inject_timeseries_into_inp(runtime_inp, injection_series, total_process)
            outlet_link_name = find_outfall_link_name(runtime_inp)
            monitor_rows = []
            outlet_rows = []
            with Simulation(str(runtime_inp)) as sim:
                sim.step_advance(STEP_SECONDS)
                nodes = Nodes(sim)
                links = Links(sim)
                node_handles = {name: nodes[name] for name in MONITOR_NODES}
                outlet_link = links[outlet_link_name]
                for step_idx, _ in enumerate(sim):
                    row = {"step": step_idx, "time": sim.current_time}
                    for monitor in MONITOR_NODES:
                        row[monitor] = float(node_handles[monitor].total_inflow)
                    monitor_rows.append(row)
                    outlet_rows.append({"step": step_idx, "time": sim.current_time, "outfall_link_flow_cms": float(outlet_link.flow)})
            return pd.DataFrame(monitor_rows), pd.DataFrame(outlet_rows)

        def evaluate_shares(shares: np.ndarray, dataset: ExperimentDataset, runtime_inp: Path):
            injection_series = shares_to_inflow_series(shares, dataset.total_process)
            event_monitor, event_outlet = run_event_simulation(runtime_inp, injection_series, dataset.total_process)
            expected_len = min(len(dataset.baseline_monitor), len(dataset.observed_delta), len(dataset.total_process), len(dataset.outlet))
            if len(event_monitor) < expected_len or len(event_outlet) < expected_len:
                return {"mean_nse": -999.0, "sse": 1.0e12, "event_monitor": dataset.baseline_monitor.iloc[:expected_len].reset_index(drop=True), "event_outlet": dataset.outlet.iloc[:expected_len].reset_index(drop=True)}
            common_len = min(len(event_monitor), len(event_outlet), expected_len)
            event_monitor = event_monitor.iloc[:common_len].reset_index(drop=True)
            sim_delta = event_monitor.copy()
            for node in MONITOR_NODES:
                sim_delta[node] = event_monitor[node].to_numpy(dtype=float) - dataset.baseline_monitor[node].to_numpy(dtype=float)[:common_len]
            nse_list = []
            sse = 0.0
            for node in MONITOR_NODES:
                obs = dataset.observed_delta[node].to_numpy(dtype=float)[:common_len]
                sim = sim_delta[node].to_numpy(dtype=float)
                denom = float(np.sum((obs - np.mean(obs)) ** 2))
                node_sse = float(np.sum((obs - sim) ** 2))
                sse += node_sse
                nse = (1.0 - node_sse / denom) if denom > 1e-12 else (1.0 if node_sse <= 1e-12 else -999.0)
                nse_list.append(nse)
            return {"mean_nse": float(np.mean(nse_list)), "sse": float(sse), "event_monitor": event_monitor, "event_outlet": event_outlet.iloc[:common_len].reset_index(drop=True)}

        generated = {
            "total_process": pd.read_csv(TOTAL_PROCESS_CSV, encoding="utf-8-sig"),
            "truth_injection": pd.read_csv(TRUTH_INJECTION_CSV, encoding="utf-8-sig"),
            "baseline_monitor": pd.read_csv(BASELINE_MONITOR_CSV, encoding="utf-8-sig"),
            "event_monitor": pd.read_csv(EVENT_MONITOR_CSV, encoding="utf-8-sig"),
            "observed_delta": pd.read_csv(OBSERVED_DELTA_CSV, encoding="utf-8-sig"),
            "outlet": pd.read_csv(OUTLET_SERIES_CSV, encoding="utf-8-sig"),
        }
        dataset = build_dataset(generated)

        truth_injection_df = extract_truth_injection_from_event_inp()
        truth_volumes = {node: float(truth_injection_df[f"{node}_volume_m3"].sum()) for node in TRUTH_INJECTION_NODES}
        total_truth = float(sum(truth_volumes.values()))
        truth_shares = np.array([truth_volumes.get(node, 0.0) / max(total_truth, 1e-12) for node in CANDIDATE_NODES], dtype=float)
        truth_result = evaluate_shares(truth_shares, dataset, runtime_model_path(0))
        print("Truth replay Mean NSE =", truth_result["mean_nse"])
        print("Truth replay SSE =", truth_result["sse"])
        """
    ).strip()

    cells = [
        md(
            """# 0401 项目全流程拆解（详细版）

这本 notebook 面向“我要自己完整运行一遍，并彻底理解项目”的目标来写。

这次会重点解决三件事：
- notebook 能从头执行通过
- 交互图能真正缩放、开关和观察
- GA / AM 的代码与结果能拆开看懂
"""
        ),
        md("## 0. 环境、模板和节点集合"),
        code(setup_code),
        code(
            dedent(
                """
                pd.DataFrame(
                    [
                        {"类别": "基线模板", "路径": str(BASELINE_MODEL_INP)},
                        {"类别": "事件模板", "路径": str(TRUTH_EVENT_MODEL_INP)},
                        {"类别": "节点表", "路径": str(LAYOUT_NODE_CSV)},
                        {"类别": "连接表", "路径": str(LAYOUT_LINK_CSV)},
                    ]
                )
                """
            ).strip()
        ),
        code(
            dedent(
                """
                print("候选井（20个）:", CANDIDATE_NODES)
                print(f"监测点（{len(MONITOR_NODES)}个）:", MONITOR_NODES)
                print("真值注水点（3个）:", TRUTH_INJECTION_NODES)
                """
            ).strip()
        ),
        md("## 1. 布设方案交互图\n\n这张图做了两层优化：\n- 用 Plotly 的交互图例作为类型开关\n- 默认只给关键节点打标签，避免挤在一起\n\n另外 `scrollZoom=True` 已开启，鼠标滚轮即可缩放。"),
        code(
            dedent(
                """
                node_df = pd.read_csv(LAYOUT_NODE_CSV, encoding="utf-8-sig")
                link_df = pd.read_csv(LAYOUT_LINK_CSV, encoding="utf-8-sig")

                role_style = {
                    "真值注水点": {"color": "#d62728", "size": 12, "symbol": "diamond"},
                    "监测点": {"color": "#1f77b4", "size": 11, "symbol": "circle"},
                    "候选布设点": {"color": "#2ca02c", "size": 9, "symbol": "circle-open"},
                    "泵站链路节点": {"color": "#ff7f0e", "size": 10, "symbol": "square"},
                    "末端关键节点": {"color": "#9467bd", "size": 12, "symbol": "star"},
                    "结构排口": {"color": "#8c564b", "size": 13, "symbol": "x"},
                    "敏感节点": {"color": "#e377c2", "size": 10, "symbol": "triangle-up"},
                    "关联节点": {"color": "#7f7f7f", "size": 5, "symbol": "circle"},
                }

                key_roles = {"真值注水点", "监测点", "候选布设点", "泵站链路节点", "末端关键节点", "结构排口", "敏感节点"}
                pos = node_df.set_index("节点名称")[["X", "Y"]].to_dict("index")
                fig = go.Figure()

                for _, row in link_df.iterrows():
                    s = row["起点"]
                    e = row["终点"]
                    if s in pos and e in pos:
                        fig.add_trace(go.Scatter(
                            x=[pos[s]["X"], pos[e]["X"]],
                            y=[pos[s]["Y"], pos[e]["Y"]],
                            mode="lines",
                            line=dict(color="rgba(100,100,100,0.18)", width=1),
                            hoverinfo="skip",
                            showlegend=False,
                        ))

                for role, sub in node_df.groupby("节点角色"):
                    style = role_style.get(role, role_style["关联节点"])
                    text = sub["节点名称"] if role in key_roles else None
                    fig.add_trace(go.Scatter(
                        x=sub["X"],
                        y=sub["Y"],
                        mode="markers+text" if role in key_roles else "markers",
                        name=role,
                        text=text,
                        textposition="top center",
                        marker=dict(color=style["color"], size=style["size"], symbol=style["symbol"]),
                        customdata=np.stack([sub["节点类型"], sub["底高程"], sub["最大水深"]], axis=1),
                        hovertemplate="节点=%{text}<br>角色=" + role + "<br>类型=%{customdata[0]}<br>底高程=%{customdata[1]}<br>最大水深=%{customdata[2]}<extra></extra>",
                    ))

                fig.update_layout(
                    title="0401 布设方案（图例可开关，滚轮可缩放）",
                    xaxis_title="X 坐标",
                    yaxis_title="Y 坐标",
                    width=1150,
                    height=900,
                    template="plotly_white",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
                )
                fig.show(config={"scrollZoom": True, "displaylogo": False})
                """
            ).strip()
        ),
        md("## 2. 真值注水提取、truth replay 与模板复现"),
        code(truth_eval_code),
        code(
            dedent(
                """
                truth_summary = pd.DataFrame(
                    {
                        "节点": list(TRUTH_INJECTION_NODES),
                        "总注水体积(m3)": [truth_injection_df[f"{node}_volume_m3"].sum() for node in TRUTH_INJECTION_NODES],
                        "峰值流量(CMS)": [truth_injection_df[f"{node}_flow_cms"].max() for node in TRUTH_INJECTION_NODES],
                    }
                )
                truth_summary["份额"] = truth_summary["总注水体积(m3)"] / truth_summary["总注水体积(m3)"].sum()
                truth_summary
                """
            ).strip()
        ),
        code(
            dedent(
                """
                total_wave = pd.DataFrame({"relative_hour": truth_injection_df["relative_hour"]})
                total_wave["total_flow_cms"] = sum(truth_injection_df[f"{node}_flow_cms"] for node in TRUTH_INJECTION_NODES)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=total_wave["relative_hour"], y=total_wave["total_flow_cms"], mode="lines", name="总注水流量"))
                fig.update_layout(title="真值总注水波形", xaxis_title="相对小时", yaxis_title="流量 (CMS)", template="plotly_white")
                fig.show(config={"scrollZoom": True, "displaylogo": False})
                """
            ).strip()
        ),
        code(
            dedent(
                """
                event_monitor_direct, event_outlet_direct = run_event_simulation(
                    runtime_model_path(1),
                    shares_to_inflow_series(truth_shares, dataset.total_process),
                    dataset.total_process,
                )
                compare_len = min(len(event_monitor_direct), len(dataset.event_monitor))
                diff_rows = []
                for node in MONITOR_NODES:
                    diff = np.max(np.abs(event_monitor_direct[node].to_numpy(dtype=float)[:compare_len] - dataset.event_monitor[node].to_numpy(dtype=float)[:compare_len]))
                    diff_rows.append({"节点": node, "最大绝对差": float(diff)})
                pd.DataFrame(diff_rows).sort_values("最大绝对差", ascending=False).reset_index(drop=True)
                """
            ).strip()
        ),
        md("## 3. 监测点“基线 vs 注水”交互曲线\n\n这一节直接从模板模型跑出监测点的 **流量 + 水深**，上面放基线、下面放注水后。"),
        code(
            dedent(
                """
                def run_model_collect_flow_depth(inp_path: Path, monitor_nodes: tuple[str, ...] = MONITOR_NODES) -> pd.DataFrame:
                    safe_name = "baseline_flow_depth.inp" if inp_path == BASELINE_MODEL_INP else "event_flow_depth.inp"
                    safe_inp = RUNTIME_DIR / safe_name
                    shutil.copyfile(inp_path, safe_inp)
                    rows = []
                    with Simulation(str(safe_inp)) as sim:
                        sim.step_advance(STEP_SECONDS)
                        nodes = Nodes(sim)
                        node_handles = {name: nodes[name] for name in monitor_nodes}
                        for step_idx, _ in enumerate(sim):
                            row = {"step": step_idx, "time": sim.current_time}
                            for node_name in monitor_nodes:
                                row[f"{node_name}_flow"] = float(node_handles[node_name].total_inflow)
                                row[f"{node_name}_depth"] = float(node_handles[node_name].depth)
                            rows.append(row)
                    return pd.DataFrame(rows)

                flow_depth_baseline = run_model_collect_flow_depth(BASELINE_MODEL_INP)
                flow_depth_event = run_model_collect_flow_depth(TRUTH_EVENT_MODEL_INP)
                curve_len = min(len(flow_depth_baseline), len(flow_depth_event), len(pd.read_csv(TOTAL_PROCESS_CSV, encoding="utf-8-sig")))
                hours = pd.read_csv(TOTAL_PROCESS_CSV, encoding="utf-8-sig")["relative_hour"].iloc[:curve_len]

                default_node = MONITOR_NODES[0]
                fig = make_subplots(
                    rows=2,
                    cols=2,
                    shared_xaxes=True,
                    subplot_titles=("基线流量", "基线水深", "注水后流量", "注水后水深"),
                    vertical_spacing=0.12,
                    horizontal_spacing=0.10,
                )

                for node in MONITOR_NODES:
                    visible = node == default_node
                    fig.add_trace(go.Scatter(x=hours, y=flow_depth_baseline[f"{node}_flow"].iloc[:curve_len], mode="lines", name=f"{node} 基线流量", visible=visible), row=1, col=1)
                    fig.add_trace(go.Scatter(x=hours, y=flow_depth_baseline[f"{node}_depth"].iloc[:curve_len], mode="lines", name=f"{node} 基线水深", visible=visible), row=1, col=2)
                    fig.add_trace(go.Scatter(x=hours, y=flow_depth_event[f"{node}_flow"].iloc[:curve_len], mode="lines", name=f"{node} 注水后流量", visible=visible), row=2, col=1)
                    fig.add_trace(go.Scatter(x=hours, y=flow_depth_event[f"{node}_depth"].iloc[:curve_len], mode="lines", name=f"{node} 注水后水深", visible=visible), row=2, col=2)

                buttons = []
                for idx, node in enumerate(MONITOR_NODES):
                    visible = [False] * (4 * len(MONITOR_NODES))
                    base = 4 * idx
                    visible[base] = True
                    visible[base + 1] = True
                    visible[base + 2] = True
                    visible[base + 3] = True
                    buttons.append(
                        dict(
                            label=node,
                            method="update",
                            args=[{"visible": visible}, {"title": f"{node}：基线 vs 注水（流量 + 水深）"}],
                        )
                    )

                fig.update_layout(
                    title=f"{default_node}：基线 vs 注水（流量 + 水深）",
                    xaxis3_title="相对小时",
                    xaxis4_title="相对小时",
                    yaxis_title="流量 (CMS)",
                    yaxis2_title="水深 (m)",
                    yaxis3_title="流量 (CMS)",
                    yaxis4_title="水深 (m)",
                    template="plotly_white",
                    width=1250,
                    height=820,
                    updatemenus=[dict(buttons=buttons, x=1.18, y=1.0)],
                )
                fig.show(config={"scrollZoom": True, "displaylogo": False})
                """
            ).strip()
        ),
        md("## 4. 当前真实源码展示"),
        md("### 数据构造脚本"),
        source_view_cell(code_dir / "build_0401_data.py"),
        md("### 模拟与评分脚本"),
        source_view_cell(code_dir / "simulation_0401.py"),
        md("### GA / AM 脚本"),
        source_view_cell(code_dir / "ga_am_0401.py"),
        md("## 4A. GA 关键函数：逐段源码 + 解释"),
        md(
            """### `initialize_populations(...)`

这个函数负责生成多种群 GA 的初始种群。

关键参数：
- `ga_population_count`：种群数量
- `ga_population_size`：每个种群包含多少个体

关键逻辑：
1. 先确定参数维度，也就是候选井数量
2. 逐个种群生成样本
3. 每个种群里，前半部分走“稀疏初始化”
4. 后半部分走 `Dirichlet` 初始化
5. 最后都投影回 simplex，保证非负且和为 1

为什么这样做：
- 稀疏初始化更容易找到“少数点主导”的解
- Dirichlet 初始化更容易覆盖“多点共同分担”的解
- 两种混合能让 GA 起跑更稳
"""
        ),
        function_source_cell(code_dir / "ga_am_0401.py", "initialize_populations"),
        md(
            """### `run_ga(...)`

这个函数是 GA 的主循环。

按顺序看：
1. 初始化多个种群
2. 每一代对每个种群做并行评估
3. 按 `mean_nse` 排序
4. 记录每代最佳和全体结果
5. 到达迁移代数时，执行：
   - `population_competition(...)`
   - `population_migration(...)`
6. 用 `evolve_population(...)` 生成下一代
7. 输出：
   - 全部样本
   - 每代最佳
   - 末代合并池
   - 全局最佳 shares

这里最重要的理解是：
GA 的任务不是直接给最终后验，而是先把“高分区域”找出来。
"""
        ),
        function_source_cell(code_dir / "ga_am_0401.py", "run_ga"),
        md(
            """### `roulette_initial_ppd(...)`

这个函数是从 GA 过渡到 AM 的桥。

按顺序看：
1. 输入是 GA 末代合并池
2. 取 `mean_nse` 当 fitness
3. 做去负平移，避免出现负概率
4. 归一化成轮盘赌概率
5. 按概率不放回抽样
6. 构建 `initial_PPD`
7. 强制确保 `ga_best_shares` 一定保留

这一步的意义：
- 不让 AM 从单个最好点起步
- 而是让 AM 从“一批高质量候选解”起步
"""
        ),
        function_source_cell(code_dir / "ga_am_0401.py", "roulette_initial_ppd"),
        md("## 4B. `initial_PPD` 交互图"),
        md(
            """下面两张图分别从两个角度看轮盘赌结果：

1. 条形图：看每个样本的 `roulette_weight`
2. 热图：看每个样本在 20 个候选节点上的份额分布

这样可以更直观看出：
- 轮盘赌保留了哪些样本
- 这些样本之间是集中在少数节点，还是多节点分散
"""
        ),
        code(
            dedent(
                """
                def top3_nodes_from_row(row: pd.Series) -> str:
                    weights = row[list(CANDIDATE_NODES)].astype(float)
                    top3 = weights.sort_values(ascending=False).head(3)
                    return ", ".join([f"{idx}:{val:.3f}" for idx, val in top3.items()])

                small_ppd = pd.read_csv(RESULT_SMALL / "0401_initial_PPD.csv", encoding="utf-8-sig")
                medium_ppd = pd.read_csv(RESULT_MEDIUM / "0401_initial_PPD.csv", encoding="utf-8-sig")

                for df in (small_ppd, medium_ppd):
                    df["sample_id"] = np.arange(1, len(df) + 1)
                    df["top3_nodes"] = df.apply(top3_nodes_from_row, axis=1)

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=small_ppd["sample_id"],
                    y=small_ppd["roulette_weight"],
                    name="small initial_PPD",
                    customdata=np.stack([small_ppd["mean_nse"], small_ppd["top3_nodes"]], axis=1),
                    hovertemplate="sample=%{x}<br>roulette_weight=%{y:.4f}<br>mean_nse=%{customdata[0]:.4f}<br>top3=%{customdata[1]}<extra></extra>",
                    visible=True,
                ))
                fig.add_trace(go.Bar(
                    x=medium_ppd["sample_id"],
                    y=medium_ppd["roulette_weight"],
                    name="medium initial_PPD",
                    customdata=np.stack([medium_ppd["mean_nse"], medium_ppd["top3_nodes"]], axis=1),
                    hovertemplate="sample=%{x}<br>roulette_weight=%{y:.4f}<br>mean_nse=%{customdata[0]:.4f}<br>top3=%{customdata[1]}<extra></extra>",
                    visible=False,
                ))
                fig.update_layout(
                    title="轮盘赌 initial_PPD 权重分布",
                    xaxis_title="样本编号",
                    yaxis_title="roulette_weight",
                    template="plotly_white",
                    width=1150,
                    height=520,
                    updatemenus=[
                        dict(
                            buttons=[
                                dict(label="small", method="update", args=[{"visible": [True, False]}, {"title": "轮盘赌 initial_PPD 权重分布 - small"}]),
                                dict(label="medium", method="update", args=[{"visible": [False, True]}, {"title": "轮盘赌 initial_PPD 权重分布 - medium"}]),
                            ],
                            x=1.02,
                            y=1.15,
                        )
                    ],
                )
                fig.show(config={"scrollZoom": True, "displaylogo": False})
                """
            ).strip()
        ),
        code(
            dedent(
                """
                small_ppd_heat = small_ppd[["sample_id", *CANDIDATE_NODES]].melt(id_vars="sample_id", var_name="node", value_name="share")
                medium_ppd_heat = medium_ppd[["sample_id", *CANDIDATE_NODES]].melt(id_vars="sample_id", var_name="node", value_name="share")

                def build_ppd_heatmap(df: pd.DataFrame, title: str):
                    pivot = df.pivot(index="node", columns="sample_id", values="share").reindex(CANDIDATE_NODES)
                    fig = go.Figure(
                        data=go.Heatmap(
                            z=pivot.to_numpy(),
                            x=list(pivot.columns),
                            y=list(pivot.index),
                            colorscale="YlOrRd",
                            colorbar_title="share",
                        )
                    )
                    fig.update_layout(title=title, xaxis_title="样本编号", yaxis_title="候选节点", template="plotly_white", width=1150, height=620)
                    fig.show(config={"scrollZoom": True, "displaylogo": False})

                build_ppd_heatmap(small_ppd_heat, "small initial_PPD 节点份额热图")
                build_ppd_heatmap(medium_ppd_heat, "medium initial_PPD 节点份额热图")
                """
            ).strip()
        ),
        md("## 4C. AM 关键函数：逐段源码 + 解释"),
        md(
            """### `sample_based_log_prior(...)`

现在这一步已经改回**更贴英文论文原文**的口径。

英文论文在贝叶斯表述里写的是：
- `p(X)` 是由 Step 1 生成的 prior information
- Step 1 对应这里的 `initial_PPD`

所以现在这个函数的作用是：
- 从 `initial_PPD` 中提取样本
- 结合 `roulette_weight`
- 用样本型核混合近似 `p(X)`

需要特别注意：
- 这里的 prior 现在是“Step 1 提供的样本型 prior”
- 但 AM 的接受率仍然按英文论文原式保留为 likelihood ratio
- 也就是说，prior 主要用于记录和解释 posterior 结构，而不是进入接受率修正
"""
        ),
        function_source_cell(code_dir / "ga_am_0401.py", "sample_based_log_prior"),
        md(
            """### `adaptive_covariance(...)`

这个函数决定 AM 每一步 proposal 的协方差。

分两段：
- 历史样本不够时：直接用 `am_initial_covariance`
- 历史样本足够时：用 `2.4**2 / d * Cov(history)` 自适应更新

含义：
- 前期先稳住
- 后期再根据链的形状自动学习步长和方向
"""
        ),
        function_source_cell(code_dir / "ga_am_0401.py", "adaptive_covariance"),
        md(
            """### `run_am(...)`

这个函数是 AM 的主循环。

按顺序看：
1. 从 `initial_PPD` 取起点
2. 计算当前状态的 `log_like / log_prior`
3. 根据 `adaptive_covariance()` 生成 proposal
4. 对 proposal 做 simplex 投影
5. 重新跑 SWMM，得到新的 `SSE / NSE`
6. 计算 proposal 的 `log_like / log_prior`
7. 用接受率决定是否接受
8. 记录到 `AM样本.csv`

当前最重要的一点：
- prior 现在来自 Step 1 的 `initial_PPD`
- 但接受率仍然按英文论文原式使用 likelihood ratio
- 所以数值上 `log_accept_ratio = proposal_log_like - current_log_like`
- 这意味着：prior 会被记录并参与 posterior 解释，但不进入接受率修正
"""
        ),
        function_source_cell(code_dir / "ga_am_0401.py", "run_am"),
        md(
            """### `extract_ppd(...)`

这个函数负责把 AM 的尾部样本变成可读的后验结果。

它会：
1. 丢掉 `warmup` 之前的样本
2. 保留 posterior tail
3. 对每个候选节点统计：
   - `posterior_mean`
   - `posterior_median`
   - `p05`
   - `p95`

也就是最后你在结果表里看到的节点后验权重汇总。
"""
        ),
        function_source_cell(code_dir / "ga_am_0401.py", "extract_ppd"),
        md("### small run 入口"),
        source_view_cell(code_dir / "run_small_0401.py"),
        md("### medium run 入口"),
        source_view_cell(code_dir / "run_medium_0401.py"),
        md("## 5. GA 与 AM 的参数解释"),
        md(
            """### GA 参数怎么理解

- `ga_population_count`：种群数。越大，平行搜索盆地越多。
- `ga_population_size`：每个种群里有多少个候选份额向量。
- `ga_generations`：GA 要迭代多少代。
- `ga_elite_ratio`：每代保留多少比例的精英个体。
- `ga_mutation_strength`：变异强度。越大，搜索更激进。
- `ga_migration_interval`：多少代做一次种群迁移。
- `ga_migration_count`：每次迁移多少个个体。
- `ga_competition_replace_count`：强种群替换弱种群的精英数。

### AM 参数怎么理解

- `am_chain_count`：AM 链数。更多链更适合看多峰，但总算量也更大。
- `am_samples_per_chain`：每条链采样长度。
- `am_warmup`：前多少步作为预热，不进入后验统计。
- `am_adapt_start`：从第几步开始自适应协方差。
- `am_initial_covariance`：初始 proposal 协方差大小，决定前期步长。
- `am_eps`：给协方差加的小正则项，防止矩阵退化。
- `posterior_validation_samples`：后验预测时抽多少组样本去重跑。

### GA 和 AM 在代码里分别做什么

GA 的职责：
1. 在 20 维 simplex 空间里快速找到高分盆地。
2. 生成一批“已经比较可信”的候选份额向量。
3. 把这批候选送进轮盘赌，形成 `initial_PPD`。

AM 的职责：
1. 从 `initial_PPD` 高概率区域附近起步。
2. 用高斯 proposal 提议一个新份额向量。
3. 把提议向量投影回 simplex。
4. 重新跑 SWMM，得到新的 `SSE / NSE`。
5. 用接受率决定 proposal 是否保留。
6. 累积形成 posterior samples，再统计 `median / P05 / P95`。

### 当前 0401 已修正的接受率

当前 prior 设为 uniform 常数，所以：

`log_accept_ratio = proposal_log_like - current_log_like`

它在数值上表现为 likelihood ratio，
但理论目的，是避免把 GA 已经使用过的数据再次当作 prior 使用。
"""
        ),
        md("## 6. 已跑好的 small / medium 结果"),
        code(
            dedent(
                """
                small_summary = json.loads((RESULT_SMALL / "0401_结果汇总.json").read_text(encoding="utf-8"))
                medium_summary = json.loads((RESULT_MEDIUM / "0401_结果汇总.json").read_text(encoding="utf-8"))
                display(pd.DataFrame([small_summary]))
                display(pd.DataFrame([medium_summary]))
                """
            ).strip()
        ),
        code(
            dedent(
                """
                small_ga = pd.read_csv(RESULT_SMALL / "0401_GA每代最佳.csv", encoding="utf-8-sig")
                fig = go.Figure()
                for pop_id, sub in small_ga.groupby("population"):
                    fig.add_trace(go.Scatter(x=sub["generation"], y=sub["best_mean_nse"], mode="lines+markers", name=f"small 种群 {pop_id}"))
                fig.update_layout(title="small run：GA 每代最佳 NSE", xaxis_title="代数", yaxis_title="最佳 Mean NSE", template="plotly_white")
                fig.show(config={"scrollZoom": True, "displaylogo": False})
                """
            ).strip()
        ),
        code(
            dedent(
                """
                medium_ga = pd.read_csv(RESULT_MEDIUM / "0401_GA每代最佳.csv", encoding="utf-8-sig")
                fig = go.Figure()
                for pop_id, sub in medium_ga.groupby("population"):
                    fig.add_trace(go.Scatter(x=sub["generation"], y=sub["best_mean_nse"], mode="lines+markers", name=f"medium 种群 {pop_id}"))
                fig.update_layout(title="medium run：GA 每代最佳 NSE", xaxis_title="代数", yaxis_title="最佳 Mean NSE", template="plotly_white")
                fig.show(config={"scrollZoom": True, "displaylogo": False})
                """
            ).strip()
        ),
        code(
            dedent(
                """
                small_post = pd.read_csv(RESULT_SMALL / "0401_后验节点权重.csv", encoding="utf-8-sig")
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=small_post["node"],
                    y=small_post["posterior_median"],
                    error_y=dict(
                        type="data",
                        symmetric=False,
                        array=small_post["p95"] - small_post["posterior_median"],
                        arrayminus=small_post["posterior_median"] - small_post["p05"],
                    ),
                ))
                fig.update_layout(title="small run：后验中位数与 90% 区间", xaxis_title="候选节点", yaxis_title="份额", template="plotly_white")
                fig.show(config={"scrollZoom": True, "displaylogo": False})
                """
            ).strip()
        ),
        md(
            """## 7. 读完以后你应该记住的 5 件事

1. 真值注水不是外编的，而是直接从事件模板提取的。
2. 评分时的注水机制必须和模板一致，都是写 `[INFLOWS] + [TIMESERIES]`。
3. 先验证 truth replay = 1，再谈 GA / AM 是否有效。
4. small run 主要看链路，medium run 才开始看后验形状。
5. 现在这套 notebook 只是教学拆解，正式大规模运行仍建议走脚本入口。
"""
        ),
    ]

    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python (LSTM)",
                "language": "python",
                "name": "lstm",
            },
            "language_info": {
                "name": "python",
                "version": "3.10",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> None:
    NOTEBOOK.parent.mkdir(parents=True, exist_ok=True)
    NOTEBOOK.write_text(json.dumps(build_notebook(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote notebook to: {NOTEBOOK}")


if __name__ == "__main__":
    main()
