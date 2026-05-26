import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, LSTM, Dense, Dropout, Attention, Concatenate, GlobalAveragePooling1D
from tensorflow.keras.callbacks import EarlyStopping
from dataclasses import dataclass
import chinese_calendar as calendar
import matplotlib.pyplot as plt

# 解决画图中文字体乱码问题
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


# ================= 1. 配置管理模块 (工业级拓扑升级) =================
@dataclass
class Config:
	base_dir: str = "RDII_Project"
	data_dir: str = os.path.join(base_dir, "data")
	model_dir: str = os.path.join(base_dir, "models")
	result_dir: str = os.path.join(base_dir, "results")
	
	# 滑动时间窗口构造训练数据，输入过去24小时(288个5分钟)，输出未来2小时(24个5分钟)
	look_back_steps: int = 288
	predict_steps: int = 24
	
	# 诊断与预警阈值体系
	rdii_q_threshold: float = 15.0  # 绝对增量阈值 (m3/h)
	ec_dilution_threshold: float = 0.15  # 电导率稀释指数阈值 (15%)
	
	# 预警分级 (相对偏离度)
	warn_light: float = 0.30
	warn_medium: float = 0.50
	warn_heavy: float = 0.70
	
	# 管网空间拓扑参数：水流从支管到主管的延迟步长 (1步=5分钟)
	delay_A_C: int = 3  # A到C需要15分钟
	delay_B_C: int = 2  # B到C需要10分钟
	
	# LSTM 模型深度定制参数
	lstm_units_1: int = 128
	lstm_units_2: int = 64
	dropout_rate: float = 0.2
	lstm_epochs: int = 30
	lstm_batch_size: int = 64
	lstm_learning_rate: float = 0.001
	
	def make_dirs(self):
		for d in [self.data_dir, self.model_dir, self.result_dir]:
			os.makedirs(d, exist_ok=True)


def get_holiday_label(date):
	if date.weekday() >= 5:
		return 1
	elif calendar.is_holiday(date):
		return 2
	else:
		return 0


# ================= 2. 数据集构建模块 (严密物理守恒) =================
def generate_multi_node_mock_data(config: Config):
	"""
	重构：生成包含A(生活区), B(工业区) -> C(主管) 的拓扑关联数据。
	严格保证质量守恒，模拟晴天偷排与雨天混接。
	"""
	print("  -> 正在生成多节点(A, B -> C)物理关联测试数据...")
	# 数据统一重采样为5分钟时间间隔
	dates = pd.date_range(start="2026-01-01", periods=25920, freq="5min")
	df = pd.DataFrame(index=dates)
	np.random.seed(42)
	
	# 全局降雨序列 R(t)
	rainfall = np.zeros(len(df))
	for _ in range(40):
		start_idx = np.random.randint(0, len(df) - 100)
		duration = np.random.randint(12, 72)
		rainfall[start_idx:start_idx + duration] = np.random.uniform(2, 10, duration)
	
	time_of_day = df.index.hour + df.index.minute / 60.0
	
	# --- 节点 A: 模拟发生雨水混接 (RDII) ---
	base_flow_A = 40 + 15 * np.sin(np.pi * (time_of_day - 8) / 12)
	base_ec_A = 800 + np.random.normal(0, 10, len(df))
	rdii_A = np.zeros(len(df))
	for i in range(1, len(df)):
		rdii_A[i] = rdii_A[i - 1] * 0.92 + rainfall[i - 1] * 3.0
	df['Q_A'] = np.maximum(base_flow_A + rdii_A + np.random.normal(0, 1, len(df)), 0)
	df['EC_A'] = base_ec_A * (base_flow_A / (df['Q_A'] + 1e-5))
	
	# --- 节点 B: 模拟发生晴天高浓度偷排 ---
	base_flow_B = 30 + 10 * np.sin(np.pi * (time_of_day - 9) / 10)
	base_ec_B = 900 + np.random.normal(0, 15, len(df))
	illicit_discharge_B = np.zeros(len(df))
	illicit_discharge_B[288 * 10: 288 * 10 + 24] = 30.0  # 某日凌晨偷排
	ec_illicit = 2500.0
	df['Q_B'] = np.maximum(base_flow_B + illicit_discharge_B + np.random.normal(0, 1, len(df)), 0)
	df['EC_B'] = np.where(illicit_discharge_B > 0,
	                      (base_ec_B * base_flow_B + ec_illicit * illicit_discharge_B) / (df['Q_B'] + 1e-5),
	                      base_ec_B)
	
	# --- 节点 C: A和B的物理汇集 (包含管网空间延迟) ---
	Q_C = np.zeros(len(df))
	EC_C = np.zeros(len(df))
	for i in range(max(config.delay_A_C, config.delay_B_C), len(df)):
		qa_delayed = df['Q_A'].iloc[i - config.delay_A_C]
		qb_delayed = df['Q_B'].iloc[i - config.delay_B_C]
		Q_C[i] = qa_delayed + qb_delayed + np.random.normal(0, 2)
		EC_C[i] = (df['EC_A'].iloc[i - config.delay_A_C] * qa_delayed +
		           df['EC_B'].iloc[i - config.delay_B_C] * qb_delayed) / (Q_C[i] + 1e-5)
	
	df['Q_C'] = np.maximum(Q_C, 0)
	df['EC_C'] = EC_C
	df['R'] = rainfall
	df['is_wet_weather'] = ((df['R'] > 0) | (rdii_A > 2.0)).astype(int)
	
	# 构造时间周期特征以反映日变化规律
	time_of_day_mins = df.index.hour * 60 + df.index.minute
	df['time_sin'] = np.sin(2 * np.pi * time_of_day_mins / 1440)
	df['time_cos'] = np.cos(2 * np.pi * time_of_day_mins / 1440)
	hour = df.index.hour
	df['peak_label'] = (((hour >= 7) & (hour <= 9)) | ((hour >= 17) & (hour <= 20))).astype(int)
	df['holiday_label'] = df.index.map(get_holiday_label)
	
	df.index.name = '时间'
	df.to_csv(os.path.join(config.data_dir, "multi_node_raw.csv"), encoding='utf-8-sig')
	return df


# ================= 3. 数据隔离与特征工程 =================
def prepare_node_data(df, node_name, config: Config):
	"""为指定节点提取特征，并严格分离出用于训练的纯干天基线数据"""
	feature_cols = [f'Q_{node_name}', f'EC_{node_name}', 'time_sin', 'time_cos', 'peak_label', 'holiday_label']
	
	# 计算干天基准电导率 EC_dry
	ec_dry_baseline = df[df['is_wet_weather'] == 0][f'EC_{node_name}'].mean()
	
	scaler = StandardScaler()
	data_scaled = scaler.fit_transform(df[feature_cols].values)
	
	X_train_dry, y_train_dry = [], []
	X_all, y_all, target_indices = [], [], []
	
	steps_total = len(data_scaled) - config.look_back_steps - config.predict_steps + 1
	
	for i in range(steps_total):
		x_window = data_scaled[i: i + config.look_back_steps]
		y_window = data_scaled[i + config.look_back_steps: i + config.look_back_steps + config.predict_steps, 0]
		target_idx = i + config.look_back_steps
		
		X_all.append(x_window)
		y_all.append(y_window)
		target_indices.append(df.index[target_idx])
		
		# 仅利用干天数据进行训练，学习正常排水规律
		if df['is_wet_weather'].iloc[target_idx] == 0:
			X_train_dry.append(x_window)
			y_train_dry.append(y_window)
	
	return (np.array(X_train_dry), np.array(y_train_dry),
	        np.array(X_all), target_indices, scaler, ec_dry_baseline)


# ================= 4. 模型构建与基线预测 =================
def build_and_train_lstm(X_train, y_train, node_name, config: Config):
	"""采用双层LSTM结构，并在第二层后引入时间注意力机制"""
	print(f"\n  -> 正在训练节点 {node_name} 的 LSTM 预测基线模型...")
	inputs = Input(shape=(X_train.shape[1], X_train.shape[2]))
	lstm1 = LSTM(units=config.lstm_units_1, return_sequences=True)(inputs)
	lstm1 = Dropout(rate=config.dropout_rate)(lstm1)
	lstm2 = LSTM(units=config.lstm_units_2, return_sequences=True)(lstm1)
	
	attention = Attention()([lstm2, lstm2])
	merged = Concatenate(axis=-1)([lstm2, attention])
	pooled = GlobalAveragePooling1D()(merged)
	outputs = Dense(units=config.predict_steps, activation='linear')(pooled)
	
	model = Model(inputs=inputs, outputs=outputs)
	# 损失函数采用均方误差（MSE），优化器为Adam
	model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=config.lstm_learning_rate), loss='mse')
	
	early_stopping = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)
	
	model.fit(X_train, y_train, epochs=config.lstm_epochs, batch_size=config.lstm_batch_size,
	          validation_split=0.2, callbacks=[early_stopping], verbose=0)
	return model


def predict_baseline(model, X_all, scaler, feature_cols_len):
	"""反归一化，输出 t+1 时刻的干天预测基线 DWF_pred"""
	y_pred_scaled = model.predict(X_all, verbose=0)[:, 0]
	dummy = np.zeros((len(y_pred_scaled), feature_cols_len))
	dummy[:, 0] = y_pred_scaled
	return scaler.inverse_transform(dummy)[:, 0]


# ================= 5. 全态时空联合溯源预警模块 =================
def spatial_temporal_diagnosis(df, pred_dict, ec_dry_dict, target_indices, config: Config):
	"""
	执行管网拓扑结构的溯源分析 与 联合异常判定
	"""
	print("\n" + "=" * 50 + "\n开启多节点全态(晴/雨)联合溯源诊断\n" + "=" * 50)
	
	# 截取与预测对齐的观测数据
	df_eval = df.loc[target_indices].copy()
	for node in ['A', 'B', 'C']:
		df_eval[f'Q_{node}_pred'] = pred_dict[node]
		# RDII(t) = Q_observed(t) − Q_DWF_pred(t)
		df_eval[f'Res_{node}'] = df_eval[f'Q_{node}'] - df_eval[f'Q_{node}_pred']
	
	diagnoses = []
	
	for i in range(max(config.delay_A_C, config.delay_B_C), len(df_eval)):
		timestamp = df_eval.index[i]
		is_wet = df_eval['is_wet_weather'].iloc[i] == 1
		
		# 提取当前主管异常，以及考虑水流演进时间的上游滞后异常
		res_C = df_eval['Res_C'].iloc[i]
		delay_res_A = df_eval['Res_A'].iloc[i - config.delay_A_C]
		delay_res_B = df_eval['Res_B'].iloc[i - config.delay_B_C]
		
		# 计算上下游差分入流
		delta_Q_segment = res_C - (delay_res_A + delay_res_B)
		
		report = {
			'时间': timestamp,
			'天气': '雨天' if is_wet else '晴天',
			'节点A_诊断': '正常', '节点B_诊断': '正常', '盲区管段(至C)_诊断': '正常',
			'预警等级': '正常'
		}
		
		max_alert_level = 0  # 1: 轻度, 2: 中度, 3: 重度
		
		# --- 针对单一节点的电导率-流量联合诊断 ---
		for node, delay, res in [('A', config.delay_A_C, delay_res_A), ('B', config.delay_B_C, delay_res_B)]:
			if res > config.rdii_q_threshold:
				obs_q = df_eval[f'Q_{node}'].iloc[i - delay]
				pred_q = df_eval[f'Q_{node}_pred'].iloc[i - delay]
				# 流量异常指数 = (Q − DWF_pred) / DWF_pred
				q_anomaly_idx = res / (pred_q + 1e-5)
				
				obs_ec = df_eval[f'EC_{node}'].iloc[i - delay]
				ec_dry = ec_dry_dict[node]
				# 电导率稀释指数 = (EC_dry − EC) / EC_dry
				ec_dilution_idx = (ec_dry - obs_ec) / ec_dry
				
				# 评估预警等级
				if q_anomaly_idx > config.warn_heavy:
					level = 3
				elif q_anomaly_idx > config.warn_medium:
					level = 2
				elif q_anomaly_idx > config.warn_light:
					level = 1
				else:
					level = 0
				max_alert_level = max(max_alert_level, level)
				
				# 联合判定
				if is_wet and ec_dilution_idx > config.ec_dilution_threshold:
					report[f'节点{node}_诊断'] = f'雨水混接(稀释度{ec_dilution_idx:.1%})'
				elif not is_wet and ec_dilution_idx < -0.15:
					report[f'节点{node}_诊断'] = f'工业偷排(浓度飙升)'
				elif not is_wet and 0 <= ec_dilution_idx <= config.ec_dilution_threshold:
					report[f'节点{node}_诊断'] = '地下水渗漏'
		
		# --- 结合管网结构的溯源分析 ---
		if delta_Q_segment > config.rdii_q_threshold:
			report['盲区管段(至C)_诊断'] = '暗管接入/盲区新增入流'
			max_alert_level = max(max_alert_level, 2)
		elif delta_Q_segment < -config.rdii_q_threshold:
			report['盲区管段(至C)_诊断'] = '严重渗漏或堵塞'
			max_alert_level = max(max_alert_level, 2)
		
		alert_map = {0: '正常', 1: '轻度异常', 2: '中度异常', 3: '重度异常'}
		report['最高预警等级'] = alert_map[max_alert_level]
		diagnoses.append(report)
	
	res_df = pd.DataFrame(diagnoses)
	res_path = os.path.join(config.result_dir, "Spatial_Temporal_Diagnosis_Report.csv")
	res_df.to_csv(res_path, index=False, encoding='utf-8-sig')
	
	# 统计分析汇总
	print(f"  -> 溯源预警完成！报告已保存至: {res_path}")
	print(f"  -> 共捕获异常事件: {(res_df['最高预警等级'] != '正常').sum()} 个时间切片")
	print(f"     - 节点A (常发混接): {(res_df['节点A_诊断'] != '正常').sum()} 次异常")
	print(f"     - 节点B (常发偷排): {(res_df['节点B_诊断'] != '正常').sum()} 次异常")
	print(f"     - 盲区管段(空间锁定): {(res_df['盲区管段(至C)_诊断'] != '正常').sum()} 次异常")
	
	return res_df


# ================= 主程序执行入口 =================
if __name__ == "__main__":
	config = Config()
	config.make_dirs()
	
	# 1. 生成物理守恒的多节点全态数据
	df = generate_multi_node_mock_data(config)
	pred_dict = {}
	ec_dry_dict = {}
	target_indices = None
	
	# 2. 对每个节点独立提取干天基线，并训练干天气候流(DWF)预测器
	for node in ['A', 'B', 'C']:
		X_train_dry, y_train_dry, X_all, indices, scaler, ec_dry = prepare_node_data(df, node, config)
		ec_dry_dict[node] = ec_dry
		print(f"  -> 节点 {node} 干天基准电导率 (EC_dry): {ec_dry:.2f}")
		# 训练该节点的 LSTM 预测模型
		model = build_and_train_lstm(X_train_dry, y_train_dry, node, config)
		# 获取该节点在所有时间步（含晴雨）的预测基线
		pred_dict[node] = predict_baseline(model, X_all, scaler, 6)
		if target_indices is None:
			target_indices = indices
	# 3. 输入实测数据与预测基线，执行综合时空拓扑溯源
	spatial_temporal_diagnosis(df, pred_dict, ec_dry_dict, target_indices, config)
	
	
	