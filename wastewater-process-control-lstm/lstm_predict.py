import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt

# Set matplotlib backend to Agg to avoid GUI errors
import matplotlib
matplotlib.use('Agg')

# Set font for Chinese characters
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False

try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

print(f"TensorFlow Version: {tf.__version__}")
print(f"Num GPUs Available: {len(tf.config.list_physical_devices('GPU'))}")

workspace_dir = r"e:\PY\射阳城北污水处理厂\东阳水厂"
csv_path = os.path.join(workspace_dir, "中控运行记录.csv")
output_plot_path = r"C:\Users\Administrator\.gemini\antigravity\brain\4ac58bc5-1718-4c97-908b-5cd1a57b476e\lstm_predictions.png"

if not os.path.exists(csv_path):
    print("CSV file not found.")
    sys.exit(1)

# ----------------- 1. Simple MinMaxScaler Implementation -----------------
class SimpleMinMaxScaler:
    def __init__(self):
        self.min_ = None
        self.max_ = None
        self.range_ = None
        
    def fit(self, X):
        self.min_ = np.nanmin(X, axis=0)
        self.max_ = np.nanmax(X, axis=0)
        self.range_ = self.max_ - self.min_
        # Prevent division by zero
        self.range_[self.range_ == 0] = 1.0
        
    def transform(self, X):
        return (X - self.min_) / self.range_
        
    def fit_transform(self, X):
        self.fit(X)
        return self.transform(X)
        
    def inverse_transform(self, X_scaled):
        return X_scaled * self.range_ + self.min_

# ----------------- 2. Load and Preprocess Data -----------------
print("Loading data...")
df = pd.read_csv(csv_path, encoding='gbk')
df['time'] = pd.to_datetime(df['time'])

print(f"Original shape: {df.shape}")
# De-duplicate timestamps by taking the mean of records with the same time
df = df.groupby('time').mean().reset_index()
df = df.sort_values('time')
print(f"Shape after de-duplication: {df.shape}")

# ----------------- 3. Time Feature Engineering -----------------
print("Engineering time features...")
df['hour'] = df['time'].dt.hour
df['weekday'] = df['time'].dt.weekday

# Cyclical encoding for hour (24 hours) and weekday (7 days)
df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24.0)
df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24.0)
df['day_sin'] = np.sin(2 * np.pi * df['weekday'] / 7.0)
df['day_cos'] = np.cos(2 * np.pi * df['weekday'] / 7.0)

# Weekend flag
df['is_weekend'] = (df['weekday'] >= 5).astype(float)

# 2026 Spring Festival Holiday flag (2026-02-13 to 2026-02-21)
df['is_holiday'] = ((df['time'] >= '2026-02-13') & (df['time'] <= '2026-02-21')).astype(float)

# List of target variables
target_cols = ['出水TN', '出水TP', '总出水NH']

# Numerical columns to scale (all SCADA variables)
num_cols = [c for c in df.columns if c not in [
    'time', 'hour', 'weekday', 'hour_sin', 'hour_cos', 'day_sin', 'day_cos', 'is_weekend', 'is_holiday'
]]
print(f"Number of SCADA numerical features: {len(num_cols)}")

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

# We also need a target-specific scaler to easily inverse-transform outputs
# Find index of target columns in num_cols
target_indices = [num_cols.index(col) for col in target_cols]

# Build input feature arrays (scaled numericals + engineered time features)
time_feat_cols = ['hour_sin', 'hour_cos', 'day_sin', 'day_cos', 'is_weekend', 'is_holiday']
train_time_feats = train_df[time_feat_cols].values
test_time_feats = test_df[time_feat_cols].values

train_features = np.hstack([train_scaled_num, train_time_feats])
test_features = np.hstack([test_scaled_num, test_time_feats])

# Extract targets (unscaled targets for sequence label creation, we will scale them using targets scaler)
train_targets_unscaled = train_df[target_cols].values
test_targets_unscaled = test_df[target_cols].values

scaler_y = SimpleMinMaxScaler()
train_targets_scaled = scaler_y.fit_transform(train_targets_unscaled)
test_targets_scaled = scaler_y.transform(test_targets_unscaled)

# ----------------- 4. Create Sliding Window Sequences -----------------
# Lookback: 72 steps (6 hours), Forecast Horizon: 24 steps (2 hours ahead)
lookback = 72
horizon = 24

def create_sequences(features, targets, lookback, horizon):
    X, y = [], []
    for i in range(len(features) - lookback - horizon + 1):
        X.append(features[i : i + lookback])
        # Predict the target at index i + lookback + horizon - 1
        y.append(targets[i + lookback + horizon - 1])
    return np.array(X), np.array(y)

print("Creating sequences...")
X_train, y_train = create_sequences(train_features, train_targets_scaled, lookback, horizon)
X_test, y_test = create_sequences(test_features, test_targets_scaled, lookback, horizon)

print(f"X_train shape: {X_train.shape}, y_train shape: {y_train.shape}")
print(f"X_test shape: {X_test.shape}, y_test shape: {y_test.shape}")

# ----------------- 5. Define and Train LSTM Model -----------------
print("Building LSTM model...")
model = Sequential([
    LSTM(64, input_shape=(X_train.shape[1], X_train.shape[2]), return_sequences=False),
    Dropout(0.2),
    Dense(32, activation='relu'),
    Dense(len(target_cols), activation='linear') # 3 outputs
])

model.compile(optimizer='adam', loss='mse', metrics=['mae'])
model.summary()

# Early stopping callback
early_stop = EarlyStopping(monitor='val_loss', patience=4, restore_best_weights=True)

print("Starting training...")
history = model.fit(
    X_train, y_train,
    epochs=15,
    batch_size=128,
    validation_split=0.1,
    callbacks=[early_stop],
    verbose=1
)

# ----------------- 6. Make Predictions and Evaluate -----------------
print("Evaluating on test set...")
y_pred_scaled = model.predict(X_test)

# Inverse transform predictions and targets to original physical units
y_pred = scaler_y.inverse_transform(y_pred_scaled)
# Get the corresponding unscaled actual targets for the test sequence
# Note: y_test corresponds to indices from lookback + horizon - 1 onwards in test set
y_true = test_targets_unscaled[lookback + horizon - 1 :]

# Calculate evaluation metrics (MAE and RMSE)
for i, col in enumerate(target_cols):
    mae = np.mean(np.abs(y_true[:, i] - y_pred[:, i]))
    rmse = np.sqrt(np.mean((y_true[:, i] - y_pred[:, i])**2))
    
    # Calculate some stats for context
    actual_mean = np.mean(y_true[:, i])
    actual_max = np.max(y_true[:, i])
    actual_min = np.min(y_true[:, i])
    
    print(f"\nMetric for {col}:")
    print(f"  MAE:  {mae:7.4f} (Mean actual: {actual_mean:7.4f}, Range: {actual_min:.2f} to {actual_max:.2f})")
    print(f"  RMSE: {rmse:7.4f}")

# ----------------- 7. Generate Evaluation Plots -----------------
print("Plotting actual vs predicted curves...")
# Plot a 500-step segment of the test set (approx 41.6 hours) for clear visualization
plot_len = 500
time_axis = test_df['time'].iloc[lookback + horizon - 1 : lookback + horizon - 1 + plot_len]

fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)

colors_actual = ['royalblue', 'forestgreen', 'darkorchid']
colors_pred = ['crimson', 'orange', 'firebrick']

for i, col in enumerate(target_cols):
    ax = axes[i]
    ax.plot(time_axis, y_true[:plot_len, i], label='实际值 (Actual)', color=colors_actual[i], alpha=0.8, linewidth=1.5)
    ax.plot(time_axis, y_pred[:plot_len, i], label='预测值 (Predicted, 2h前瞻)', color=colors_pred[i], linestyle='--', linewidth=1.5)
    
    # Add a horizontal line for emission standard reference if applicable
    if col == '出水TN':
        ax.axhline(y=10.0, color='gray', linestyle=':', label='一级A排放标准 (10.0)')
    elif col == '出水TP':
        ax.axhline(y=0.5, color='gray', linestyle=':', label='一级A排放标准 (0.5)')
    elif col == '总出水NH':
        ax.axhline(y=5.0, color='gray', linestyle=':', label='一级A排放标准 (5.0)')
        
    ax.set_title(f"{col} 实际值 vs 2小时前瞻预测值 对比 (测试集片段)")
    ax.set_ylabel(f"{col} (mg/L)")
    ax.legend(loc='upper right')
    ax.grid(True, linestyle='--', alpha=0.5)

plt.xlabel("时间 (Time)")
plt.tight_layout()
plt.savefig(output_plot_path, dpi=150)
plt.close()

print(f"Evaluation plot successfully saved to {output_plot_path}")
print("Done!")
