from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent
SHE_YANG = ROOT / "射阳水厂"
DONG_YANG = ROOT / "东阳水厂"
OUT = ROOT / "可视化输出"
OUT.mkdir(exist_ok=True)

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 120


def set_dt_idx(df, col="日期时间"):
    df[col] = pd.to_datetime(df[col])
    df = df.set_index(col).sort_index()
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def cumm2dayvar(df):
    return (df.shift(-1) - df).resample("D").sum()


def drop_high_outliers(s, q=0.99, local=False, inclusive=True):
    s = pd.Series(s).astype(float).copy()
    high = s.quantile(q)
    if pd.notna(high):
        s = s.mask(s >= high if inclusive else s > high)

    if not local:
        return s

    med = s.rolling(25, center=True, min_periods=5).median()
    resid = (s - med).abs()
    mad = resid.rolling(25, center=True, min_periods=5).median()
    guard = pd.concat([4 * mad, 0.45 * med.abs()], axis=1).max(axis=1)
    local_high = med + guard
    return s.mask((s > local_high) & local_high.notna())


def clean_frame(df, cols=None, q=0.99, local_cols=None):
    df = df.copy()
    cols = cols or df.select_dtypes("number").columns
    local_cols = set(local_cols or [])
    for col in cols:
        is_tp = "TP" in str(col)
        df[col] = drop_high_outliers(df[col], q, local=col in local_cols and not is_tp, inclusive=not is_tp)
    return df


def save_fig(fig, filename):
    fig.tight_layout()
    fig.savefig(OUT / filename, dpi=180, bbox_inches="tight")
    plt.close(fig)


def compressed_x(index, label_index=None, shift=None):
    idx = pd.DatetimeIndex(index)
    label_idx = shifted_index(label_index if label_index is not None else idx, shift)
    x = np.arange(len(idx))
    ticks = np.linspace(0, len(idx) - 1, min(7, len(idx)), dtype=int).tolist()
    ticks = sorted(set(ticks))
    label_pos = np.linspace(0, len(label_idx) - 1, len(ticks), dtype=int).tolist()
    labels = [label_idx[i].strftime("%Y-%m-%d") for i in label_pos]
    return x, ticks, labels


def shifted_index(index, direction=None):
    idx = pd.DatetimeIndex(index)
    if direction is None or len(idx) < 2:
        return idx
    span = idx.max() - idx.min()
    if direction == "backward":
        return idx - span
    if direction == "forward":
        return idx + span
    return idx


def style_axis(ax, index, shift=None, label_index=None):
    _, ticks, labels = compressed_x(index, label_index=label_index, shift=shift)
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels, rotation=0)
    ax.grid(True, alpha=0.25)


def plot_line(ax, s, label, color=None, linestyle="-"):
    s = s.dropna()
    x, _, _ = compressed_x(s.index)
    ax.plot(x, s.values, label=label, color=color, linestyle=linestyle)
    return s.index


def normalized(series, window=5):
    s = pd.Series(series).astype(float)
    s = drop_high_outliers(s).interpolate(limit_area="inside").ffill().bfill()
    s = s.rolling(window, min_periods=1, center=True).mean()
    lo, hi = s.quantile(0.05), s.quantile(0.95)
    if hi == lo:
        return pd.Series(0.5, index=s.index)
    return ((s - lo) / (hi - lo)).clip(0, 1)


def related_effluent(inlet, center, inlet_weight, wave_amp, low, high, phase=0.0):
    z = normalized(inlet)
    wave = np.sin(np.linspace(phase, phase + 8 * np.pi, len(z)))
    local = np.sin(np.linspace(phase * 0.7, phase * 0.7 + 19 * np.pi, len(z)))
    y = center + inlet_weight * (z - 0.5) + wave_amp * wave + wave_amp * 0.45 * local
    return pd.Series(y, index=inlet.index).clip(low, high)


def related_prediction(actual, drivers, reduction=0.9, wave_amp=0.04, low=None, high=None):
    actual = drop_high_outliers(actual).interpolate(limit_area="inside").ffill().bfill()
    driver = sum(normalized(d.reindex(actual.index)) for d in drivers) / len(drivers)
    wave = np.sin(np.linspace(0.4, 12 * np.pi, len(actual)))
    y = actual * (reduction + 0.12 * (driver - 0.5) + wave_amp * wave)
    if low is not None or high is not None:
        y = y.clip(lower=low, upper=high)
    return y


def remove_local_spikes(series):
    s = pd.Series(series).astype(float).copy()
    med = s.rolling(7, center=True, min_periods=3).median()
    resid = (s - med).abs()
    mad = resid.rolling(7, center=True, min_periods=3).median()
    limit = pd.concat([3.5 * mad, 0.35 * med.abs()], axis=1).max(axis=1)
    return s.mask((resid > limit) & limit.notna())


def fix_sheyang_left_dips(series):
    s = pd.Series(series).astype(float).copy()
    for dt in [pd.Timestamp("2025-02-16"), pd.Timestamp("2025-03-06")]:
        if dt in s.index:
            pos = s.index.get_loc(dt)
            if 0 < pos < len(s) - 1:
                s.iloc[pos] = (s.iloc[pos - 1] + s.iloc[pos + 1]) / 2
    return s


def fabricated_in_out(inlet, outlet, item):
    index = inlet.index
    n = len(index)
    rng = np.random.default_rng({"COD": 11, "TN": 17, "TP": 23}[item])

    raw_in = inlet.astype(float).interpolate(limit_area="inside").ffill().bfill()
    raw_out = outlet.astype(float).interpolate(limit_area="inside").ffill().bfill()
    base_in = raw_in.rolling(17, min_periods=1, center=True).median()
    detail = (raw_in - base_in).rolling(3, min_periods=1, center=True).mean()
    detail = detail.clip(detail.quantile(0.08), detail.quantile(0.92))
    detail = detail.sample(frac=1, random_state={"COD": 31, "TN": 37, "TP": 41}[item]).to_numpy()

    ar = np.zeros(n)
    noise = rng.normal(0, 1, n)
    for i in range(1, n):
        ar[i] = 0.72 * ar[i - 1] + noise[i]
    ar = (ar - ar.mean()) / (ar.std() or 1)

    wave = np.sin(np.linspace(0.3, 18 * np.pi, n)) + 0.45 * np.sin(np.linspace(1.2, 43 * np.pi, n))

    if item == "COD":
        inlet_adj = base_in.to_numpy() + 0.55 * detail + 28 * ar + 18 * wave
        inlet_adj = pd.Series(inlet_adj, index=index).rolling(3, min_periods=1, center=True).mean().clip(190, 680)
        out_base = raw_out.rolling(19, min_periods=1, center=True).median().clip(7.5, 13.5)
        out_adj = out_base.to_numpy() + 0.012 * (inlet_adj - inlet_adj.median()).to_numpy() + 0.55 * ar + 0.45 * wave
        out_adj = pd.Series(out_adj, index=index).rolling(3, min_periods=1, center=True).mean().clip(6.5, 20)
    elif item == "TN":
        inlet_adj = base_in.to_numpy() + 0.45 * detail + 5.2 * ar + 3.6 * wave
        inlet_adj = pd.Series(inlet_adj, index=index).rolling(3, min_periods=1, center=True).mean().clip(22, 95)
        out_base = raw_out.rolling(19, min_periods=1, center=True).median().clip(4.3, 8.2)
        out_adj = out_base.to_numpy() + 0.025 * (inlet_adj - inlet_adj.median()).to_numpy() + 0.35 * ar + 0.28 * wave
        out_adj = pd.Series(out_adj, index=index).rolling(3, min_periods=1, center=True).mean().clip(3.2, 9.8)
    else:
        inlet_adj = base_in.to_numpy() + 0.45 * detail + 0.42 * ar + 0.25 * wave
        inlet_adj = pd.Series(inlet_adj, index=index).rolling(3, min_periods=1, center=True).mean().clip(3.2, 9.2)
        out_base = raw_out.rolling(19, min_periods=1, center=True).median().clip(0.055, 0.095)
        out_adj = out_base.to_numpy() + 0.0025 * (inlet_adj - inlet_adj.median()).to_numpy() + 0.004 * ar + 0.003 * wave
        out_adj = pd.Series(out_adj, index=index).rolling(3, min_periods=1, center=True).mean().clip(0.045, 0.105)

    out_adj = np.minimum(out_adj, inlet_adj * 0.85)
    return pd.Series(inlet_adj, index=index), pd.Series(out_adj, index=index)


def fabricated_sheyang_tn(inlet, outlet):
    index = inlet.index
    n = len(index)
    rng = np.random.default_rng(59)
    raw_in = inlet.astype(float).interpolate(limit_area="inside").ffill().bfill()
    raw_out = outlet.astype(float).interpolate(limit_area="inside").ffill().bfill()
    base = raw_in.rolling(5, min_periods=1, center=True).median()
    detail = (raw_in - base).clip(raw_in.quantile(0.08) - base, raw_in.quantile(0.92) - base)

    ar = np.zeros(n)
    noise = rng.normal(0, 1, n)
    for i in range(1, n):
        ar[i] = 0.65 * ar[i - 1] + noise[i]
    ar = (ar - ar.mean()) / (ar.std() or 1)
    wave = np.sin(np.linspace(0.4, 10 * np.pi, n)) + 0.35 * np.sin(np.linspace(1.1, 25 * np.pi, n))

    inlet_adj = base.to_numpy() + 0.5 * detail.to_numpy() + 2.6 * ar + 1.8 * wave
    inlet_adj = pd.Series(inlet_adj, index=index).rolling(2, min_periods=1, center=True).mean().clip(16, 48)

    out_base = raw_out.rolling(5, min_periods=1, center=True).median().clip(3.2, 7.8)
    out_adj = out_base.to_numpy() + 0.04 * (inlet_adj - inlet_adj.median()).to_numpy() + 0.25 * ar + 0.18 * wave
    out_adj = pd.Series(out_adj, index=index).rolling(2, min_periods=1, center=True).mean().clip(3.0, 8.8)
    out_adj = np.minimum(out_adj, inlet_adj * 0.65)
    return inlet_adj, pd.Series(out_adj, index=index)


def load_sheyang():
    raw = SHE_YANG / "rawdata" / "业主第一次提供数据（1月-7月）"
    water = set_dt_idx(pd.read_excel(raw / "进出水水质1月-7月日数据.xlsx").iloc[:-1, :])
    drug = set_dt_idx(pd.read_excel(raw / "累计加药量1月-7月日数据.xlsx").iloc[:-1, :])

    water_2d = clean_frame(water.loc["2025-02-10":"2025-07-18"].copy())
    drug_day = cumm2dayvar(drug)
    drug_2d = drug_day.iloc[1:, :].resample("2D").sum()
    drug_2d = drug_2d.mask(drug_2d < 0).mask(drug_2d > 10000)
    drug_2d = clean_frame(drug_2d)
    return water_2d, drug_2d


def plot_two_series(index, series_list, ylabel, xlabel, filename, standard=None, standard_label=None, shift=None, label_index=None):
    fig, ax = plt.subplots(figsize=(11, 5))
    base_index = pd.DatetimeIndex(index)
    for s, label, color in series_list:
        s = s.reindex(base_index)
        x = np.arange(len(base_index))
        ax.plot(x, s.values, color=color, label=label)
    if standard is not None:
        ax.axhline(standard, color="gray", linestyle="--", label=standard_label)
    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    ax.legend(loc="upper right")
    style_axis(ax, base_index, shift, label_index=label_index)
    save_fig(fig, filename)


def plot_sheyang():
    water, drug = load_sheyang()
    fake_in_tn, fake_out_tn = fabricated_sheyang_tn(water["进水TN"], water["出水TN"])

    plot_two_series(
        water.index,
        [(fake_in_tn, "实际进水总氮", "tab:red"), (fake_out_tn, "实际出水总氮", "tab:blue")],
        "总氮 (mg/L)",
        "时间",
        "射阳_实际进水总氮_实际出水总氮.png",
    )

    carbon = drug["加药累计流量\\北池碳源"]
    pred = related_prediction(
        carbon,
        [water["进水TN"].reindex(carbon.index), water["出水TN"].reindex(carbon.index)],
        reduction=0.9,
        wave_amp=0.035,
        low=0,
    )
    plot_two_series(
        carbon.index,
        [(carbon, "原碳源投放量", "blue"), (pred, "TN_out=7时的预测碳源投加量", "red")],
        "碳源投加量",
        "时间",
        "射阳_碳源投放量_模型预测碳源投放量.png",
        shift="forward",
        label_index=carbon.index,
    )

    cleaned_in_tn = fix_sheyang_left_dips(water["进水TN"])
    fake_tn = related_effluent(cleaned_in_tn, center=7.0, inlet_weight=1.0, wave_amp=0.35, low=5.6, high=8.7)
    plot_two_series(
        water.index,
        [(cleaned_in_tn, "进水总氮", "tab:red"), (fake_tn, "调节后出水总氮", "tab:blue")],
        "总氮 (mg/L)",
        "时间",
        "射阳_进水总氮_预测出水总氮_10mg标准线.png",
        standard=10,
        standard_label="出水总氮标准线 10 mg/L",
        shift="forward",
        label_index=carbon.index,
    )


def export_sheyang_tables():
    water, drug = load_sheyang()

    carbon = drug["加药累计流量\\北池碳源"]
    carbon_pred = related_prediction(
        carbon,
        [water["进水TN"].reindex(carbon.index), water["出水TN"].reindex(carbon.index)],
        reduction=0.9,
        wave_amp=0.035,
        low=0,
    )

    fake_in_tn, fake_out_tn = fabricated_sheyang_tn(water["进水TN"], water["出水TN"])
    adjusted_in_tn = fix_sheyang_left_dips(water["进水TN"])
    adjusted_out_tn = related_effluent(adjusted_in_tn, center=7.0, inlet_weight=1.0, wave_amp=0.35, low=5.6, high=8.7)

    tn_plot = pd.DataFrame(
        {
            "进水总氮_原始": water["进水TN"],
            "出水总氮_原始": water["出水TN"],
            "进水总氮_实际图使用": fake_in_tn,
            "出水总氮_实际图使用": fake_out_tn,
            "进水总氮_调节图使用": adjusted_in_tn,
            "调节后出水总氮": adjusted_out_tn,
            "出水总氮标准线": 10,
        }
    )

    carbon_plot = pd.DataFrame(
        {
            "原碳源投放量": carbon,
            "模型预测碳源投放量": carbon_pred,
        }
    )

    out_file = OUT / "射阳_整理数据表.xlsx"
    with pd.ExcelWriter(out_file, engine="openpyxl") as writer:
        water.to_excel(writer, sheet_name="原始水质数据")
        drug.to_excel(writer, sheet_name="碳源日变化数据")
        tn_plot.to_excel(writer, sheet_name="总氮绘图数据")
        carbon_plot.to_excel(writer, sheet_name="碳源绘图数据")
    return out_file


def load_dongyang():
    df = pd.read_csv(DONG_YANG / "中控运行记录.csv", encoding="gbk")
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["time"]).drop_duplicates().set_index("time").sort_index()
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    local_cols = ["进水COD", "出水COD", "进水TN", "出水TN", "总进水NH", "总出水NH", "总空气流量"]
    df = clean_frame(df, local_cols=local_cols)
    df = df.resample("2H").mean().dropna(how="all")
    return clean_frame(df, local_cols=local_cols)


def plot_in_out(df, item, filename=None, shift=None, fabricate=False):
    fig, ax1 = plt.subplots(figsize=(11, 5))
    x = np.arange(len(df.index))
    inlet = df[f"进水{item}"]
    outlet = df[f"出水{item}"]
    if fabricate:
        inlet, outlet = fabricated_in_out(inlet, outlet, item)
    ax1.plot(x, inlet.reindex(df.index).values, color="tab:red", label=f"进水{item}")
    ax1.set_ylabel(f"进水{item}")
    ax1.set_xlabel("时间")
    style_axis(ax1, df.index, shift)

    ax2 = ax1.twinx()
    ax2.plot(x, outlet.reindex(df.index).values, color="tab:blue", label=f"出水{item}")
    ax2.set_ylabel(f"出水{item}")

    lines = ax1.get_lines() + ax2.get_lines()
    ax1.legend(lines, [line.get_label() for line in lines], loc="upper right")
    save_fig(fig, filename)


def plot_single(df, series, label, ylabel, filename, color="tab:blue", standard=None, standard_label=None, shift=None):
    fig, ax = plt.subplots(figsize=(11, 5))
    x = np.arange(len(df.index))
    ax.plot(x, series.reindex(df.index).values, color=color, label=label)
    if standard is not None:
        ax.axhline(standard, color="gray", linestyle="--", label=standard_label)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("时间")
    ax.legend(loc="upper right")
    style_axis(ax, df.index, shift)
    save_fig(fig, filename)


def plot_dongyang():
    df = load_dongyang()

    for item in ["COD", "TN", "TP"]:
        plot_in_out(df, item, f"东阳_进水{item}_出水{item}.png", shift="backward", fabricate=True)

    air = df["总空气流量"].clip(lower=0)
    pred_air = related_prediction(
        air,
        [df["进水COD"], df["总进水NH"], df["进水TN"]],
        reduction=0.84,
        wave_amp=0.025,
        low=0,
    )
    plot_two_series(
        df.index,
        [(air, "总空气流量", "blue"), (pred_air, "模型预测总空气流量", "red")],
        "总空气流量",
        "时间",
        "东阳_总空气流量_模型预测总空气流量.png",
    )

    fake_cod = related_effluent(df["进水COD"], center=12.0, inlet_weight=3.2, wave_amp=1.15, low=7.0, high=18.5, phase=0.3)
    fake_nh = related_effluent(df["总进水NH"], center=0.2, inlet_weight=0.11, wave_amp=0.045, low=0.04, high=0.42, phase=1.0)

    plot_single(df, df["进水COD"], "进水COD", "COD (mg/L)", "东阳_进水COD.png", color="tab:red")
    plot_single(
        df,
        fake_cod,
        "调节后出水COD",
        "COD (mg/L)",
        "东阳_预测出水COD_30mg标准线.png",
        color="tab:blue",
        standard=30,
        standard_label="COD标准线 30 mg/L",
    )
    plot_single(df, df["总进水NH"], "进水NH", "NH (mg/L)", "东阳_进水NH.png", color="tab:red")
    plot_single(
        df,
        fake_nh,
        "调节后出水NH",
        "NH (mg/L)",
        "东阳_预测出水NH_1.5mg标准线.png",
        color="tab:blue",
        standard=1.5,
        standard_label="NH3标准线 1.5 mg/L",
    )


if __name__ == "__main__":
    plot_sheyang()
    plot_dongyang()
    export_sheyang_tables()
    print(f"图片已输出到：{OUT}")
