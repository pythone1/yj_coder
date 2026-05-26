"""
项目名称: wastewater-lstm-control
技术领域: 04-smart-water-systems
模块说明: carbon_dosing_optimizer.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

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
output_plot_path = os.path.join(workspace_dir, "carbon_dosing_optimization.png")
brain_artifacts_dir = r"C:\Users\Administrator\.gemini\antigravity\brain\4ac58bc5-1718-4c97-908b-5cd1a57b476e"

print("Loading LSTM model and scaling parameters...")
model = tf.keras.models.load_model(model_path, custom_objects={'Attention': Attention})
with open(scalers_path, "rb") as f:
    scalers = pickle.load(f)

scaler_x = scalers["scaler_x"]
scaler_y = scalers["scaler_y"]
num_cols = scalers["num_cols"]
target_cols = scalers["target_cols"]
time_feat_cols = scalers["time_feat_cols"]

# Identify column indices
carbon_col = "B系列碳源投加流量"
carbon_idx = num_cols.index(carbon_col)
flow_col = "总进水"
flow_idx = num_cols.index(flow_col)
in_tn_col = "进水TN"
in_tn_idx = num_cols.index(in_tn_col)
out_tn_col = "出水TN"
out_tn_idx = num_cols.index(out_tn_col)

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

# Predict TN
print("Running LSTM forward pass to forecast effluent TN...")
preds_scaled = model.predict(X_test)
preds = scaler_y.inverse_transform(preds_scaled)
pred_tn = preds[:, 0] # Predicted effluent TN at t + 24

# Reconstruct time series indices for aligned analysis
# For sequence i, the prediction is at step i + lookback + horizon - 1
test_indices_t = np.arange(lookback - 1, len(test_df) - horizon)
test_df_t = test_df.iloc[test_indices_t].copy()
test_time_axis = test_df_t['time'].values

# Get actual values
actual_flow = test_df_t[flow_col].values
actual_in_tn = test_df_t[in_tn_col].values
actual_out_tn = test_df_t[out_tn_col].values
actual_dosing = test_df_t[carbon_col].values

# Target threshold for effluent TN
tn_target = 8.5

# Feedforward controller gain calibration
train_flow = train_df[flow_col].values
train_in_tn = train_df[in_tn_col].values
train_out_tn = train_df[out_tn_col].values
train_dosing = train_df[carbon_col].values

train_load_removed = train_flow * np.maximum(0, train_in_tn - train_out_tn)
train_active_mask = train_load_removed > 0.1
K_ff = np.sum(train_dosing[train_active_mask]) / np.sum(train_load_removed[train_active_mask])
print(f"Feedforward gain K_ff: {K_ff:.6f}")

# Calculate Feedforward dosing
in_load_to_remove = actual_flow * np.maximum(0, actual_in_tn - tn_target)
dosing_ff = K_ff * in_load_to_remove

# Calculate Feedback dosing (K_fb = 0.3 provides a responsive yet stable control action)
# Capped feedback: limit negative feedback to at most 15% of the feedforward value to ensure process safety in industrial operation
K_fb = 0.3
dosing_fb = K_fb * (pred_tn - tn_target)
dosing_fb_capped = np.maximum(-0.15 * dosing_ff, dosing_fb)

# Total Recommended Dosing
dosing_rec = dosing_ff + dosing_fb_capped

# Clip recommended dosing to [0, 4.5] (maximum pump capacity is 4.5 m3/h)
dosing_rec = np.clip(dosing_rec, 0.0, 4.5)

# Calculate savings percentage
# The data is sampled every 5 minutes, so total volume in m3 is sum(flow_rate) * 5/60
actual_total_vol = np.sum(actual_dosing) * 5.0 / 60.0
rec_total_vol = np.sum(dosing_rec) * 5.0 / 60.0
savings_vol = actual_total_vol - rec_total_vol
savings_pct = savings_vol / actual_total_vol * 100

print(f"\n--- Optimization Recommendation Model Evaluation ---")
print(f"Test period: {len(test_df_t)} steps (about {len(test_df_t)*5/60/24:.2f} days)")
print(f"Total Actual Carbon Source Dosed: {actual_total_vol:.2f} m3")
print(f"Total Recommended Carbon Source:  {rec_total_vol:.2f} m3")
print(f"Carbon Source Saved:              {savings_vol:.2f} m3 ({savings_pct:.2f}%)")

# Economic calculation
# Typical compound carbon source cost is about 1500 Yuan / m3
price_per_m3 = 1500.0
saved_cost_test_period = savings_vol * price_per_m3
annual_saved_cost = (saved_cost_test_period / (len(test_df_t)*5/60/24)) * 365.0

print(f"Economic Value:")
print(f"  Test Period Savings: {saved_cost_test_period:.2f} Yuan")
print(f"  Projected Annual Savings: {annual_saved_cost:.2f} Yuan (~{annual_saved_cost/10000:.1f}万元)")

# Save optimization results to CSV
opt_df = pd.DataFrame({
    'time': test_df_t['time'],
    'influent_flow_m3_h': actual_flow,
    'influent_tn_mg_L': actual_in_tn,
    'actual_effluent_tn_mg_L': actual_out_tn,
    'predicted_effluent_tn_2h_mg_L': pred_tn,
    'actual_carbon_dosing_m3_h': actual_dosing,
    'recommended_carbon_dosing_m3_h': dosing_rec
})
opt_csv_path = os.path.join(workspace_dir, "carbon_dosing_optimization_results.csv")
opt_df.to_csv(opt_csv_path, index=False, encoding='gbk')
print(f"\nOptimization results saved to {opt_csv_path}")

# Plotting the results
print("Generating visualization plots...")
plot_len = len(test_df_t)  # Plot the entire test period
time_plot = test_time_axis[:plot_len]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

# Panel 1: TN values
ax1.plot(time_plot, actual_out_tn[:plot_len], label='实际出水 TN (Actual)', color='royalblue', linewidth=1.8)
ax1.plot(time_plot, pred_tn[:plot_len], label='LSTM 2小时前瞻预测 TN (Predicted)', color='crimson', linestyle='--', linewidth=1.5)
ax1.axhline(y=10.0, color='red', linestyle=':', label='一级A排放标准 (10.0 mg/L)', alpha=0.8)
ax1.axhline(y=tn_target, color='orange', linestyle='-.', label='AI 内控安全阈值 (8.5 mg/L)', alpha=0.8)
# Zoom in to keep TN curve readable and clear
max_tn_val = max(actual_out_tn[:plot_len].max(), pred_tn[:plot_len].max(), 10.0)
ax1.set_ylim(0.0, max_tn_val + 1.0)
ax1.set_ylabel("出水总氮 TN (mg/L)", fontsize=12)
ax1.set_title("出水总氮 TN 实际值 vs 2小时前瞻预测值 (前馈预测反馈控制基础)", fontsize=14)
ax1.legend(loc='upper right')
ax1.grid(True, linestyle='--', alpha=0.5)

# Panel 2: Carbon dosing comparison
ax2.plot(time_plot, actual_dosing[:plot_len], label='历史实际碳源投加流量 (Actual)', color='darkorchid', linewidth=1.8)
ax2.plot(time_plot, dosing_rec[:plot_len], label='AI 推荐最优碳源投加流量 (Recommended)', color='forestgreen', linestyle='-', linewidth=1.5)
ax2.set_ylabel("碳源投加流量 (m3/h)", fontsize=12)
ax2.set_title("历史实际投药量 vs AI 智能推荐最优投药量对比", fontsize=14)
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.5)

plt.xlabel("时间 (Time)", fontsize=12)
plt.tight_layout()
plt.savefig(output_plot_path, dpi=150)
plt.close()
print(f"Optimization comparison plot saved to {output_plot_path}")

# Copy plot to brain artifacts directory for easy access
shutil.copy(output_plot_path, os.path.join(brain_artifacts_dir, "carbon_dosing_optimization.png"))
print("Plot successfully copied to brain artifacts directory.")
