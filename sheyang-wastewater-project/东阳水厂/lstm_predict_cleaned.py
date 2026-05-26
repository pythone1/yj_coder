import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt

import matplotlib
matplotlib.use('Agg')
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False

try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Layer, Input
from tensorflow.keras.callbacks import EarlyStopping
import tensorflow.keras.backend as K

class Attention(Layer):
    def __init__(self, **kwargs):
        super(Attention, self).__init__(**kwargs)
        
    def build(self, input_shape):
        self.W = self.add_weight(name="att_weight", shape=(input_shape[-1], 1), initializer="glorot_uniform", trainable=True)
        self.b = self.add_weight(name="att_bias", shape=(input_shape[1], 1), initializer="zeros", trainable=True)
        super(Attention, self).build(input_shape)
        
    def call(self, x):
        # x shape: (batch_size, seq_len, num_features)
        # e = tanh(x * W + b) -> shape: (batch_size, seq_len, 1)
        e = K.tanh(K.dot(x, self.W) + self.b)
        # a = softmax(e) -> shape: (batch_size, seq_len, 1)
        a = K.softmax(e, axis=1)
        # output = sum(x * a, axis=1) -> shape: (batch_size, num_features)
        output = x * a
        return K.sum(output, axis=1)

workspace_dir = r"e:\PY\射阳城北污水处理厂\东阳水厂"
csv_path = os.path.join(workspace_dir, "中控运行记录.csv")
output_plot_path = os.path.join(workspace_dir, "lstm_predictions.png")

# 1. MinMaxScaler
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

# 2. Load and Clean Data
print("Loading and cleaning data...")
df = pd.read_csv(csv_path, encoding='gbk')
df['time'] = pd.to_datetime(df['time'])
df = df.groupby('time').mean().reset_index().sort_values('time')

# --- REFINED DATA PREPROCESSING ---
print("Applying refined data preprocessing...")

# List of target variables
target_cols = ['出水TN', '出水TP', '总出水NH']

# Numerical columns (all SCADA variables)
num_cols = [c for c in df.columns if c not in ['time', 'hour', 'weekday']]

# A. Handle negative values (physically impossible for flows/concentrations, except ORP)
non_negative_cols = [c for c in num_cols if 'ORP' not in c]
for col in non_negative_cols:
    neg_mask = df[col] < 0
    if neg_mask.sum() > 0:
        print(f"  Replacing {neg_mask.sum()} negative values in {col} with NaN and interpolating.")
        df.loc[neg_mask, col] = np.nan
        df[col] = df[col].interpolate(method='linear').bfill().ffill()

# B. Clean sensor calibration dead-ends/outliers for targets
# For TN: standard is < 10, anything > 12 is likely calibration or outlier
tn_mask = df['出水TN'] > 12.0
print(f"  Replacing {tn_mask.sum()} outliers in 出水TN with interpolated values.")
df.loc[tn_mask, '出水TN'] = np.nan
df['出水TN'] = df['出水TN'].interpolate(method='linear').bfill().ffill()

# For NH: standard is < 5, 95% is < 0.17. Anything > 1.0 is outlier
nh_mask = df['总出水NH'] > 1.0
print(f"  Replacing {nh_mask.sum()} outliers in 总出水NH with interpolated values.")
df.loc[nh_mask, '总出水NH'] = np.nan
df['总出水NH'] = df['总出水NH'].interpolate(method='linear').bfill().ffill()

# For TP: standard is < 0.5, 95% is < 0.10. Anything > 0.15 is outlier
tp_mask = df['出水TP'] > 0.15
print(f"  Replacing {tp_mask.sum()} outliers in 出水TP with interpolated values.")
df.loc[tp_mask, '出水TP'] = np.nan
df['出水TP'] = df['出水TP'].interpolate(method='linear').bfill().ffill()

# C. Apply a rolling median-mean filter to smooth high-frequency sensor noise on features
# We apply this only to the input features (non-target columns) to preserve prediction integrity
features_to_smooth = [col for col in num_cols if col not in target_cols]
print("  Smoothing features using rolling median-mean filter (median window=3, mean window=3)...")
for col in features_to_smooth:
    # First apply median filter to remove impulsive spikes/outliers
    median_smoothed = df[col].rolling(window=3, min_periods=1, center=True).median()
    # Then apply mean filter to smooth high-frequency measurement noise
    df[col] = median_smoothed.rolling(window=3, min_periods=1, center=True).mean()

# 3. Time Feature Engineering (Removing Holiday & Weekend Tags)
print("Engineering cyclical time features (hour only)...")
df['hour'] = df['time'].dt.hour
df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24.0)
df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24.0)

# Chronological split (80% train, 20% test)
train_size = int(len(df) * 0.8)
train_df = df.iloc[:train_size].copy()
test_df = df.iloc[train_size:].copy()

print(f"Train size: {len(train_df)} rows")
print(f"Test size: {len(test_df)} rows")

# Scale SCADA numerical features
scaler_x = SimpleMinMaxScaler()
train_scaled_num = scaler_x.fit_transform(train_df[num_cols].values)
test_scaled_num = scaler_x.transform(test_df[num_cols].values)

# Build input feature arrays (scaled numericals + engineered diurnal time features)
time_feat_cols = ['hour_sin', 'hour_cos']
train_features = np.hstack([train_scaled_num, train_df[time_feat_cols].values])
test_features = np.hstack([test_scaled_num, test_df[time_feat_cols].values])

# Extract targets
train_targets_unscaled = train_df[target_cols].values
test_targets_unscaled = test_df[target_cols].values

scaler_y = SimpleMinMaxScaler()
train_targets_scaled = scaler_y.fit_transform(train_targets_unscaled)
test_targets_scaled = scaler_y.transform(test_targets_unscaled)

# Create sequences
# Lookback: 144 steps (12 hours), Forecast Horizon: 24 steps (2 hours ahead)
lookback = 144
horizon = 24

def create_sequences(features, targets, lookback, horizon):
    X, y = [], []
    for i in range(len(features) - lookback - horizon + 1):
        X.append(features[i : i + lookback])
        y.append(targets[i + lookback + horizon - 1])
    return np.array(X), np.array(y)

print("Creating sequences...")
X_train, y_train = create_sequences(train_features, train_targets_scaled, lookback, horizon)
X_test, y_test = create_sequences(test_features, test_targets_scaled, lookback, horizon)

# 4. Model Definition
inputs = Input(shape=(X_train.shape[1], X_train.shape[2]))
lstm_out = LSTM(64, return_sequences=True)(inputs)
att_out = Attention()(lstm_out)
x = Dropout(0.2)(att_out)
x = Dense(32, activation='relu')(x)
outputs = Dense(len(target_cols), activation='linear')(x)

model = Model(inputs=inputs, outputs=outputs)

model.compile(optimizer='adam', loss='mse', metrics=['mae'])
early_stop = EarlyStopping(monitor='val_loss', patience=4, restore_best_weights=True)

# Train model
print("Training LSTM model on refined data...")
history = model.fit(
    X_train, y_train,
    epochs=15,
    batch_size=128,
    validation_split=0.1,
    callbacks=[early_stop],
    verbose=1
)

# Evaluate
print("Generating predictions...")
y_pred_scaled = model.predict(X_test)
y_pred = scaler_y.inverse_transform(y_pred_scaled)
y_true = test_targets_unscaled[lookback + horizon - 1 :]

# Output metrics
for i, col in enumerate(target_cols):
    mae = np.mean(np.abs(y_true[:, i] - y_pred[:, i]))
    rmse = np.sqrt(np.mean((y_true[:, i] - y_pred[:, i])**2))
    print(f"\nFinal Metric for {col}:")
    print(f"  MAE:  {mae:7.4f} (Mean actual: {np.mean(y_true[:, i]):7.4f}, Range: {np.min(y_true[:, i]):.2f} to {np.max(y_true[:, i]):.2f})")
    print(f"  RMSE: {rmse:7.4f}")

# Plot results
print("Generating prediction plots...")
plot_len = len(y_true)
time_axis = test_df['time'].iloc[lookback + horizon - 1 : lookback + horizon - 1 + plot_len]

fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
colors_actual = ['royalblue', 'forestgreen', 'darkorchid']
colors_pred = ['crimson', 'orange', 'firebrick']

for i, col in enumerate(target_cols):
    ax = axes[i]
    ax.plot(time_axis, y_true[:plot_len, i], label='实际值 (Actual)', color=colors_actual[i], alpha=0.8, linewidth=1.5)
    ax.plot(time_axis, y_pred[:plot_len, i], label='预测值 (Predicted, 2h前瞻)', color=colors_pred[i], linestyle='--', linewidth=1.5)
    
    if col == '出水TN':
        ax.axhline(y=10.0, color='red', linestyle=':', label='一级A排放标准 (10.0)')
        max_val = max(y_true[:plot_len, i].max(), y_pred[:plot_len, i].max(), 10.0)
        ax.set_ylim(0.0, max_val + 1.0)
    elif col == '出水TP':
        # Zoom in to actual data variation (0.05-0.12 mg/L)
        max_val = max(y_true[:plot_len, i].max(), y_pred[:plot_len, i].max())
        ax.set_ylim(0.0, max(max_val * 1.3, 0.15))
        ax.text(0.02, 0.88, '一级A排放标准 (0.50 mg/L) 超出上方图表范围', transform=ax.transAxes, color='red', fontsize=10, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
    elif col == '总出水NH':
        # Zoom in to actual data variation (0.05-0.30 mg/L)
        max_val = max(y_true[:plot_len, i].max(), y_pred[:plot_len, i].max())
        ax.set_ylim(0.0, max(max_val * 1.5, 0.50))
        ax.text(0.02, 0.88, '一级A排放标准 (5.00 mg/L) 超出上方图表范围', transform=ax.transAxes, color='red', fontsize=10, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
        
    ax.set_title(f"{col} 实际值 vs 2小时前瞻预测值 (精细预处理 - 去除节假日特征)")
    ax.set_ylabel(f"{col} (mg/L)")
    ax.legend(loc='upper right')
    ax.grid(True, linestyle='--', alpha=0.5)

plt.xlabel("时间 (Time)")
plt.tight_layout()
plt.savefig(output_plot_path, dpi=150)
plt.close()

print(f"Refined predictions plot successfully saved to {output_plot_path}")

# Save the trained model and scalers
model_save_path = os.path.join(workspace_dir, "lstm_model.h5")
scalers_save_path = os.path.join(workspace_dir, "scalers.pkl")

print(f"Saving model to {model_save_path}...")
model.save(model_save_path)

print(f"Saving scalers to {scalers_save_path}...")
import pickle
with open(scalers_save_path, "wb") as f:
    pickle.dump({
        "scaler_x": scaler_x,
        "scaler_y": scaler_y,
        "num_cols": num_cols,
        "target_cols": target_cols,
        "time_feat_cols": time_feat_cols
    }, f)

print("Model and scalers saved successfully!")
print("Model update complete!")
