import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import matplotlib.pyplot as plt

# ==========================================
# 污水处理厂精确加药 LSTM 模型基准训练模板（TensorFlow / Keras）
# ==========================================
# 本脚本由 AI 自动生成，使用本地已有的 TensorFlow 环境。
# 演示如何利用合并后的时序数据进行滑动窗口数据集构建、模型定义、训练与预测。
# 由于历史投加量（如乙酸钠、PAC）尚未拿到，脚本中构建了基于工艺机理的“模拟加药量”
# 用于打通数据管道。一旦拿到真实加药量数据，只需替换相应列即可。

def prepare_data(inlet_path, outlet_path, window_size=12, lead_time=4):
    """
    读取合并水质数据，并构建时序滑动窗口数据集。
    window_size: 历史回溯的小时数（这里设为12小时，模拟水力延迟和工艺惯性）
    lead_time: 预测未来的步长（这里设为4小时，用于超前预警或前馈控制）
    """
    df_in = pd.read_csv(inlet_path)
    df_out = pd.read_csv(outlet_path)
    
    # 时序对齐
    df_in['time'] = pd.to_datetime(df_in['time'])
    df_out['time'] = pd.to_datetime(df_out['time'])
    
    # 合并进水和出水数据
    df = pd.merge(df_in, df_out, on='time', suffixes=('_in', '_out'))
    df = df.sort_values('time').reset_index(drop=True)
    
    # ----------------------------------------------------
    # 模拟数据填充：在缺少加药量数据时，我们根据反硝化机理公式添加一个“模拟乙酸钠加药量”列
    # 理论公式：所需外加碳源量 = 理论总碳源需求 - 进水自带碳源
    # 模拟估算：乙酸钠加药量 (L/h) ≈ 进水流量 (t/h) * (进水TN * 3.5 - 进水COD) * 修正系数
    # 这仅用于测试代码！
    df['mock_acetate_dosing'] = df['flow_in'] * (df['TN_conc_in'] * 3.5 - df['COD_conc_in']).clip(lower=0) * 0.05
    df['mock_acetate_dosing'] = df['mock_acetate_dosing'].fillna(df['mock_acetate_dosing'].mean())
    
    # 准备特征 (Inputs) 和目标 (Targets)
    # 输入特征：进水流量、进水COD、进水TN、水温、当前加药量
    feature_cols = ['flow_in', 'COD_conc_in', 'TN_conc_in', 'temp_in', 'mock_acetate_dosing']
    # 预测目标：未来的出水总氮 (TN_out)
    target_col = 'TN_conc_out'
    
    X_data = df[feature_cols].values
    y_data = df[target_col].values
    
    # 特征标准化
    scaler_x = StandardScaler()
    scaler_y = StandardScaler()
    
    X_scaled = scaler_x.fit_transform(X_data)
    y_scaled = scaler_y.fit_transform(y_data.reshape(-1, 1)).flatten()
    
    X_seq, y_seq = [], []
    # 构建滑动窗口数据集
    for i in range(len(df) - window_size - lead_time + 1):
        # 历史的 window_size 小时的特征
        X_seq.append(X_scaled[i : i + window_size])
        # 未来的第 lead_time 小时的出水TN
        y_seq.append(y_scaled[i + window_size + lead_time - 1])
        
    return np.array(X_seq), np.array(y_seq), scaler_x, scaler_y, df['time'].iloc[window_size + lead_time - 1:].reset_index(drop=True)

def main():
    inlet_path = r"E:\PY\research\0520\智慧水务资料\scratch\inlet_consolidated.csv"
    outlet_path = r"E:\PY\research\0520\智慧水务资料\scratch\outlet_consolidated.csv"
    
    if not (os.path.exists(inlet_path) and os.path.exists(outlet_path)):
        print("未找到合并后的CSV文件，请确认已运行数据合并脚本 consolidate_data.py！")
        return
        
    print("正在加载和处理数据...")
    window_size = 12  # 回溯 12 小时
    lead_time = 4     # 预测 4 小时后
    
    X, y, scaler_x, scaler_y, time_index = prepare_data(inlet_path, outlet_path, window_size, lead_time)
    print(f"时序数据集构建完毕. 特征集形状: {X.shape}, 标签集形状: {y.shape}")
    
    # 划分训练集和测试集（时序数据应按时间先后划分，不能用随机 K-fold）
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    # 建立 Keras LSTM 模型
    print("构建 TensorFlow LSTM 模型...")
    model = Sequential([
        LSTM(64, activation='tanh', return_sequences=True, input_shape=(X.shape[1], X.shape[2])),
        Dropout(0.2),
        LSTM(32, activation='tanh', return_sequences=False),
        Dropout(0.2),
        Dense(1)
    ])
    
    model.compile(optimizer='adam', loss='mse')
    model.summary()
    
    # 训练模型
    print("开始模型训练...")
    history = model.fit(
        X_train, y_train,
        epochs=15,
        batch_size=32,
        validation_split=0.1,
        verbose=1
    )
        
    # 测试评估
    print("\n评估测试集...")
    preds_scaled = model.predict(X_test)
    preds = scaler_y.inverse_transform(preds_scaled).flatten()
    actuals = scaler_y.inverse_transform(y_test.reshape(-1, 1)).flatten()
        
    # 计算评估指标
    rmse = np.sqrt(np.mean((preds - actuals) ** 2))
    mae = np.mean(np.abs(preds - actuals))
    print(f"\n测试集模型评估结果: RMSE={rmse:.3f} mg/L, MAE={mae:.3f} mg/L")
    
    # 绘制预测对比图
    plt.figure(figsize=(12, 6))
    plt.plot(actuals[:120], label='Actual Outlet TN', color='blue', alpha=0.7)
    plt.plot(preds[:120], label='Predicted Outlet TN (LSTM)', color='red', linestyle='--', alpha=0.9)
    plt.title('Outlet Total Nitrogen (TN) Prediction - First 120 Hours of Test Set')
    plt.xlabel('Time Step (Hours)')
    plt.ylabel('Concentration (mg/L)')
    plt.legend()
    plt.grid(True)
    
    plot_path = r"E:\PY\research\0520\智慧水务资料\scratch\lstm_prediction_plot.png"
    plt.savefig(plot_path, dpi=300)
    print(f"预测结果对比图已保存至 {plot_path}")
    
    # ----------------------------------------------------
    # 如何用于加药优化控制？（控制策略核心提示）
    # ----------------------------------------------------
    # 一旦 LSTM 能够准确根据进水特征和加药量预测出水 TN:
    # 我们可以通过以下步骤寻优：
    # Given: 当前历史特征 X_history (由传感器实时读取)
    # Goal: 寻找一个乙酸钠加药量 d_opt, 使得预测的 TN_out_pred = model(X_history + d_opt) 满足限值并达到用药最小。
    # 我们可以用网格搜索或二分法在 [d_min, d_max] 区间寻优，找到让预测出水 TN 恰好安全达标（例如 11-12 mg/L）的最少加药量。

if __name__ == "__main__":
    main()
