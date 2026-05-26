import pickle
import os
import sys
import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt
import shutil
from tensorflow.keras.layers import Layer
import tensorflow.keras.backend as K

class Attention(Layer):
    def __init__(self, **kwargs):
        super(Attention, self).__init__(**kwargs)
        
    def build(self, input_shape):
        self.W = self.add_weight(name="att_weight", shape=(input_shape[-1], 1), initializer="glorot_uniform", trainable=True)
        self.b = self.add_weight(name="att_bias", shape=(input_shape[1], 1), initializer="zeros", trainable=True)
        super(Attention, self).build(input_shape)
        
    def call(self, x):
        e = K.tanh(K.dot(x, self.W) + self.b)
        a = K.softmax(e, axis=1)
        output = x * a
        return K.sum(output, axis=1)

import matplotlib
matplotlib.use('Agg')
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False

try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

class SimpleMinMaxScaler:
    def __init__(self):
        self.min_ = None
        self.max_ = None
        self.range_ = None
    def fit(self, X):
        self.min_ = np.nanmin(X, axis=0)
        self.max_ = np.nanmax(X, axis=0)
        self.range_ = self.max_ - self.min_
        self.range_[self.range_ == 0] = 1.0
    def transform(self, X):
        return (X - self.min_) / self.range_
    def fit_transform(self, X):
        self.fit(X)
        return self.transform(X)
    def inverse_transform(self, X_scaled):
        return X_scaled * self.range_ + self.min_

workspace_dir = r"e:\PY\射阳城北污水处理厂\东阳水厂"
model_path = os.path.join(workspace_dir, "lstm_model.h5")
scalers_path = os.path.join(workspace_dir, "scalers.pkl")
csv_path = os.path.join(workspace_dir, "中控运行记录.csv")
output_plot_path = os.path.join(workspace_dir, "pac_dosing_optimization.png")
brain_artifacts_dir = r"C:\Users\Administrator\.gemini\antigravity\brain\4ac58bc5-1718-4c97-908b-5cd1a57b476e"

print("Loading LSTM model and scaling parameters for PAC optimization...")
model = tf.keras.models.load_model(model_path, custom_objects={'Attention': Attention})
with open(scalers_path, "rb") as f:
    scalers = pickle.load(f)

scaler_x = scalers["scaler_x"]
scaler_y = scalers["scaler_y"]
num_cols = scalers["num_cols"]
target_cols = scalers["target_cols"]
time_feat_cols = scalers["time_feat_cols"]

# Identify column indices
pac_col = "PAC实际投加量"
pac_idx = num_cols.index(pac_col)
flow_col = "总进水"
flow_idx = num_cols.index(flow_col)
in_tp_filter_col = "反硝化滤池进TP"
in_tp_filter_idx = num_cols.index(in_tp_filter_col)
out_tp_col = "出水TP"
out_tp_idx = num_cols.index(out_tp_col)

# Load and clean data
print("Loading and preprocessing data...")
df = pd.read_csv(csv_path, encoding='gbk')
df['time'] = pd.to_datetime(df['time'])
df = df.groupby('time').mean().reset_index().sort_values('time')

# Preprocessing
target_cols_to_clean = ['出水TN', '出水TP', '总出水NH']
non_negative_cols = [c for c in num_cols if 'ORP' not in c]
for col in non_negative_cols:
    neg_mask = df[col] < 0
    if neg_mask.sum() > 0:
        df.loc[neg_mask, col] = np.nan
        df[col] = df[col].interpolate(method='linear').bfill().ffill()

df.loc[df['出水TN'] > 12.0, '出水TN'] = np.nan
df['出水TN'] = df['出水TN'].interpolate(method='linear').bfill().ffill()

df.loc[df['总出水NH'] > 1.0, '总出水NH'] = np.nan
df['总出水NH'] = df['总出水NH'].interpolate(method='linear').bfill().ffill()

df.loc[df['出水TP'] > 0.15, '出水TP'] = np.nan
df['出水TP'] = df['出水TP'].interpolate(method='linear').bfill().ffill()

features_to_smooth = [col for col in num_cols if col not in target_cols_to_clean]
for col in features_to_smooth:
    median_smoothed = df[col].rolling(window=3, min_periods=1, center=True).median()
    df[col] = median_smoothed.rolling(window=3, min_periods=1, center=True).mean()

df['hour'] = df['time'].dt.hour
df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24.0)
df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24.0)

# Chronological split
train_size = int(len(df) * 0.8)
train_df = df.iloc[:train_size].copy()
test_df = df.iloc[train_size:].copy()

test_scaled_num = scaler_x.transform(test_df[num_cols].values)
test_features = np.hstack([test_scaled_num, test_df[time_feat_cols].values])

lookback = 144
horizon = 24

def create_sequences(features, lookback):
    X = []
    for i in range(len(features) - lookback - horizon + 1):
        X.append(features[i : i + lookback])
    return np.array(X)

X_test = create_sequences(test_features, lookback)

# Predict TP
print("Running LSTM forward pass to forecast effluent TP...")
preds_scaled = model.predict(X_test)
preds = scaler_y.inverse_transform(preds_scaled)
pred_tp = preds[:, 1] # Predicted effluent TP at t + 24 (index 1 is TP)

# Reconstruct time series indices for aligned analysis
test_indices_t = np.arange(lookback - 1, len(test_df) - horizon)
test_df_t = test_df.iloc[test_indices_t].copy()
test_time_axis = test_df_t['time'].values

# Get actual values at step t
actual_flow = test_df_t[flow_col].values
actual_in_tp_filter = test_df_t[in_tp_filter_col].values
actual_out_tp = test_df_t[out_tp_col].values
actual_dosing_pac = test_df_t[pac_col].values

# Target threshold for effluent TP (Safety Inner-Control Line)
tp_target = 0.09

# Feedforward controller gain calibration from training set
train_flow = train_df[flow_col].values
train_in_tp_filter = train_df[in_tp_filter_col].values
train_out_tp = train_df[out_tp_col].values
train_dosing_pac = train_df[pac_col].values

train_load_removed_pac = train_flow * np.maximum(0, train_in_tp_filter - train_out_tp)
train_active_mask = train_load_removed_pac > 0.01
K_ff_pac = np.sum(train_dosing_pac[train_active_mask]) / np.sum(train_load_removed_pac[train_active_mask])
print(f"PAC Feedforward gain K_ff_pac: {K_ff_pac:.6f}")

# Calculate Feedforward PAC dosing
in_load_to_remove_pac = actual_flow * np.maximum(0, actual_in_tp_filter - tp_target)
dosing_ff_pac = K_ff_pac * in_load_to_remove_pac

# Calculate Feedback PAC dosing (K_fb_pac = 5.0 to compensate for small scale of TP value differences)
# Capped feedback: limit negative feedback to at most 15% of the feedforward value to ensure process safety in industrial operation
K_fb_pac = 5.0
dosing_fb_pac = K_fb_pac * (pred_tp - tp_target)
dosing_fb_pac_capped = np.maximum(-0.15 * dosing_ff_pac, dosing_fb_pac)

# Total Recommended PAC Dosing
dosing_rec_pac = dosing_ff_pac + dosing_fb_pac_capped

# Clip recommended dosing to [0.0, 12.0] (maximum pump capacity is 12.0 m3/h)
dosing_rec_pac = np.clip(dosing_rec_pac, 0.0, 12.0)

# Calculate savings percentage
actual_total_vol = np.sum(actual_dosing_pac) * 5.0 / 60.0
rec_total_vol = np.sum(dosing_rec_pac) * 5.0 / 60.0
savings_vol = actual_total_vol - rec_total_vol
savings_pct = savings_vol / actual_total_vol * 100

print(f"\n--- PAC Dosing Recommendation Model Evaluation ---")
print(f"Test period: {len(test_df_t)} steps (about {len(test_df_t)*5/60/24:.2f} days)")
print(f"Total Actual PAC Dosed: {actual_total_vol:.2f} m3")
print(f"Total Recommended PAC:  {rec_total_vol:.2f} m3")
print(f"PAC Saved:              {savings_vol:.2f} m3 ({savings_pct:.2f}%)")

# Economic calculation
# Typical PAC (polyaluminum chloride) chemical cost is about 1200 Yuan / m3
price_per_m3_pac = 1200.0
saved_cost_test_period = savings_vol * price_per_m3_pac
annual_saved_cost = (saved_cost_test_period / (len(test_df_t)*5/60/24)) * 365.0

print(f"Economic Value:")
print(f"  Test Period Savings: {saved_cost_test_period:.2f} Yuan")
print(f"  Projected Annual Savings: {annual_saved_cost:.2f} Yuan (~{annual_saved_cost/10000:.1f}万元)")

# Save optimization results to CSV
opt_df = pd.DataFrame({
    'time': test_df_t['time'],
    'influent_flow_m3_h': actual_flow,
    'filter_inlet_tp_mg_L': actual_in_tp_filter,
    'actual_effluent_tp_mg_L': actual_out_tp,
    'predicted_effluent_tp_2h_mg_L': pred_tp,
    'actual_pac_dosing_m3_h': actual_dosing_pac,
    'recommended_pac_dosing_m3_h': dosing_rec_pac
})
opt_csv_path = os.path.join(workspace_dir, "pac_dosing_optimization_results.csv")
opt_df.to_csv(opt_csv_path, index=False, encoding='gbk')
print(f"\nPAC Optimization results saved to {opt_csv_path}")

# Plotting the results
print("Generating visualization plots...")
plot_len = len(test_df_t)  # Plot the entire test period
time_plot = test_time_axis[:plot_len]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

# Panel 1: TP values
ax1.plot(time_plot, actual_out_tp[:plot_len], label='实际出水 TP (Actual)', color='forestgreen', linewidth=1.8)
ax1.plot(time_plot, pred_tp[:plot_len], label='LSTM 2小时前瞻预测 TP (Predicted)', color='orange', linestyle='--', linewidth=1.5)
ax1.axhline(y=tp_target, color='purple', linestyle='-.', label='AI 内控安全阈值 (0.09 mg/L)', alpha=0.8)
# Zoom in to actual data variation (0.05-0.12 mg/L) to prevent squashing by the 0.50 mg/L standard line
max_tp_val = max(actual_out_tp[:plot_len].max(), pred_tp[:plot_len].max())
ax1.set_ylim(0.0, max(max_tp_val * 1.3, 0.15))
ax1.text(0.02, 0.88, '一级A排放标准 (0.50 mg/L) 超出上方图表范围', transform=ax1.transAxes, color='red', fontsize=10, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
ax1.set_ylabel("出水总磷 TP (mg/L)", fontsize=12)
ax1.set_title("出水总磷 TP 实际值 vs 2小时前瞻预测值 (前馈预测反馈控制基础)", fontsize=14)
ax1.legend(loc='upper right')
ax1.grid(True, linestyle='--', alpha=0.5)

# Panel 2: PAC dosing comparison
ax2.plot(time_plot, actual_dosing_pac[:plot_len], label='历史实际 PAC 投加流量 (Actual)', color='royalblue', linewidth=1.8)
ax2.plot(time_plot, dosing_rec_pac[:plot_len], label='AI 推荐最优 PAC 投加流量 (Recommended)', color='crimson', linestyle='-', linewidth=1.5)
ax2.set_ylabel("PAC 投加流量 (m3/h)", fontsize=12)
ax2.set_title("历史实际投药量 vs AI 智能推荐最优 PAC 投药量对比", fontsize=14)
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.5)

plt.xlabel("时间 (Time)", fontsize=12)
plt.tight_layout()
plt.savefig(output_plot_path, dpi=150)
plt.close()
print(f"PAC Optimization comparison plot saved to {output_plot_path}")

# Copy plot to brain artifacts directory for easy access
shutil.copy(output_plot_path, os.path.join(brain_artifacts_dir, "pac_dosing_optimization.png"))
print("Plot successfully copied to brain artifacts directory.")
