import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, LSTM, Dense, Dropout, Attention, Concatenate, GlobalAveragePooling1D
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import matplotlib.pyplot as plt
import joblib
from dataclasses import dataclass
import chinese_calendar as calendar

# 解决画图中文字体乱码问题
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


# ================= 1. 配置管理模块 =================
@dataclass
class Config:
	"""集中管理所有路径与超参数"""
	base_dir: str = "RDII_Project"
	data_dir: str = os.path.join(base_dir, "data")
	model_dir: str = os.path.join(base_dir, "models")
	result_dir: str = os.path.join(base_dir, "results")
	
	# 原始模拟数据路径
	data_path: str = os.path.join(data_dir, "RDII_full_data.csv")
	# 处理后带有完整特征标签的数据集保存路径
	processed_data_path: str = os.path.join(data_dir, "RDII_processed_features.csv")
	
	# 窗口与特征参数
	look_back_steps: int = 288  # 滑动窗口输入：过去24小时(288个5分钟步长)
	predict_steps: int = 24  # 预测输出：未来2小时(24个5分钟步长)
	target_col_idx: int = 0  # 流量 Q 在训练特征组中的索引（去除了降雨特征后）
	
	# 指标判定阈值 (用于判断是否存在雨污入流)
	rdii_q_threshold: float = 15.0  # 指标1：流量差值大于 15 m³/h 视为异常增量
	ec_drop_threshold: float = 700.0  # 指标2：电导率低于 700 μS/cm 视为受到雨水稀释
	ec_dilution_threshold: float = 0.15  # 【新增】：电导率稀释指数 > 15% 视为显著下降
	
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
	# 法定节假日（包括调休后的假日）
	if date.weekday() >= 5:
		return 1
	# 普通周末
	elif calendar.is_holiday(date):
		return 2
	else:
		return 0


# ================= 2. 数据集构建模块 =================
def generate_mock_data(config: Config):
	"""
	生成3个月包含晴雨交替的测试数据
	干天：规律的日变化流量，高电导率。
	雨天：有降雨，流量激增，电导率被稀释下降。
	"""
	print(f"  -> 正在生成含有晴/雨特征的测试数据，路径: {config.data_path}")
	dates = pd.date_range(start="2026-01-01", periods=25920, freq="5min")
	df = pd.DataFrame(index=dates)
	
	np.random.seed(42)
	# 生成降雨序列
	rainfall = np.zeros(len(df))
	for _ in range(40):  # 模拟40场雨
		start_idx = np.random.randint(0, len(df) - 100)
		duration = np.random.randint(12, 72)
		intensity = np.random.uniform(2, 10)
		rainfall[start_idx:start_idx + duration] = intensity * np.random.rand(duration)
	
	# 生成规律的干天生活用水基线 (早晚双高峰)
	time_of_day = df.index.hour + df.index.minute / 60.0
	base_flow = 80 + 30 * np.sin(np.pi * (time_of_day - 8) / 12) + 20 * np.sin(np.pi * (time_of_day - 8) / 6)
	
	# 模拟雨污入流 (RDII)
	rdii = np.zeros(len(df))
	for i in range(1, len(df)):
		rdii[i] = rdii[i - 1] * 0.92 + rainfall[i - 1] * 5.0  # 衰减系数0.92，降雨转换系数5.0
	
	flow = base_flow + rdii + np.random.normal(0, 2, len(df))  # 实际总流量
	base_ec = 800 + np.random.normal(0, 10, len(df))  # 旱天基线电导率约为 800
	ec = base_ec * (base_flow / (base_flow + rdii + 1))  # 电导率被大量雨水稀释
	
	df['R'] = rainfall
	df['Q'] = np.maximum(flow, 0)
	df['EC'] = ec
	
	# 标记【晴雨天标签】：降雨量>0或降雨后RDII仍较高的时间段标记为雨天(1)，否则为干天(0)
	df['is_wet_weather'] = ((df['R'] > 0) | (rdii > 5.0)).astype(int)
	
	df.index.name = '时间'
	df.to_csv(config.data_path, encoding='utf-8-sig')
	return df


def preprocess_data(config: Config):
	"""提取周期特征，构建完整的特征表格"""
	df = pd.read_csv(config.data_path, index_col='时间', parse_dates=True)
	time_of_day = df.index.hour * 60 + df.index.minute
	df['time_sin'] = np.sin(2 * np.pi * time_of_day / 1440)
	df['time_cos'] = np.cos(2 * np.pi * time_of_day / 1440)
	hour = df.index.hour
	df['peak_label'] = ((hour >= 7) & (hour <= 9)) | ((hour >= 17) & (hour <= 20))
	df['peak_label'] = df['peak_label'].astype(int)
	# 保留您的节假日自定义函数逻辑
	df['holiday_label'] = df.index.map(get_holiday_label)
	
	# 【新增】：将处理好包含所有特征的数据表单独保存出来
	df.to_csv(config.processed_data_path, encoding='utf-8-sig')
	print(f"  -> 处理后的完整特征数据集已保存至: {config.processed_data_path}")
	
	return df


# ================= 3. 面向干湿分离的特征工程 =================
def create_sequences_for_baseline(df, feature_cols, scaler, config: Config):
	data_scaled = scaler.transform(df[feature_cols].values)
	
	X_dry, y_dry = [], []  # 用于训练干天基线
	X_wet, y_wet, wet_dates, wet_ec = [], [], [], []  # 用于雨天测试与入流诊断
	
	steps_total = len(data_scaled) - config.look_back_steps - config.predict_steps + 1
	
	# 【新增逻辑】：计算干天基准电导率 EC_dry (取所有干天时段电导率的均值)
	ec_dry_baseline = df[df['is_wet_weather'] == 0]['EC'].mean()
	
	for i in range(steps_total):
		x_window = data_scaled[i: i + config.look_back_steps]
		y_window = data_scaled[i + config.look_back_steps: i + config.look_back_steps + config.predict_steps,
		           config.target_col_idx]
		
		target_idx = i + config.look_back_steps
		is_wet = df['is_wet_weather'].iloc[target_idx] == 1
		
		if not is_wet:
			X_dry.append(x_window)
			y_dry.append(y_window)
		else:
			X_wet.append(x_window)
			y_wet.append(y_window)
			wet_dates.append(df.index[target_idx])
			wet_ec.append(df['EC'].iloc[target_idx])
	
	return np.array(X_dry), np.array(y_dry), np.array(X_wet), np.array(y_wet), np.array(wet_dates), np.array(
		wet_ec), ec_dry_baseline


# ================= 4. 模型评估与入流双指标诊断模块 =================
def evaluate_and_diagnose_rdii(X_test, y_test, test_dates, test_ec, ec_dry_baseline, model, model_name, feature_cols,
                               scaler, config: Config):
	"""模型预测干天基线，计算诊断指标，生成附带入流标签的数据集"""
	print(f"\n  -> 开始对 {model_name} 进行雨天数据预测与入流诊断...")
	# 针对非深度学习模型需要展平
	if len(X_test.shape) == 3 and model_name in ["Linear_Regression", "Random_Forest"]:
		X_test_input = X_test.reshape(X_test.shape[0], -1)
	else:
		X_test_input = X_test
	
	y_pred = model.predict(X_test_input)
	
	y_pred_t1 = y_pred[:, 0]
	y_test_t1 = y_test[:, 0]
	
	# 反归一化
	dummy_pred = np.zeros((len(y_pred_t1), len(feature_cols)))
	dummy_pred[:, config.target_col_idx] = y_pred_t1
	y_pred_dwf = scaler.inverse_transform(dummy_pred)[:, config.target_col_idx]  # DWF_pred
	y_pred_dwf = np.maximum(y_pred_dwf, 1e-5)  # 防止除数为0
	
	dummy_true = np.zeros((len(y_test_t1), len(feature_cols)))
	dummy_true[:, config.target_col_idx] = y_test_t1
	y_true_q = scaler.inverse_transform(dummy_true)[:, config.target_col_idx]  # Q_observed
	
	# ================= 核心：计算两大指标与判别 =================
	# 指标1：流量异常指数 = (Q - DWF_pred) / DWF_pred
	flow_anomaly_index = (y_true_q - y_pred_dwf) / y_pred_dwf
	
	# 指标2：电导率稀释指数 = (EC_dry - EC) / EC_dry
	ec_dilution_index = (ec_dry_baseline - test_ec) / ec_dry_baseline
	
	warning_levels = []
	diagnosis_types = []
	
	for q_idx, ec_idx in zip(flow_anomaly_index, ec_dilution_index):
		# 预警分级
		if q_idx > 0.7:
			w_level = "重度异常"
		elif q_idx > 0.5:
			w_level = "中度异常"
		elif q_idx > 0.3:
			w_level = "轻度异常"
		else:
			w_level = "正常"
		
		# 异常类型诊断
		if q_idx > 0.3:
			if ec_idx > config.ec_dilution_threshold:
				diag = "混接风险(雨水侵入)"
			else:
				diag = "地下水渗透风险"
		else:
			diag = "无显著异常"
		
		warning_levels.append(w_level)
		diagnosis_types.append(diag)
	
	# 生成最终加标签的表格
	result_df = pd.DataFrame({
		'时间': test_dates,
		f'实际流量_Q': y_true_q,
		f'干天预测基线_DWF_pred': y_pred_dwf,
		'实际电导率_EC': test_ec,
		'干天基准电导率_EC_dry': ec_dry_baseline,
		'流量异常指数': flow_anomaly_index,
		'电导率稀释指数': ec_dilution_index,
		'入流预警等级': warning_levels,
		'溯源异常诊断': diagnosis_types
	})
	
	csv_path = os.path.join(config.result_dir, f"{model_name}_Diagnostic_Result.csv")
	result_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
	
	# 【新增打印信息统计分析】：
	total_anomalies = (np.array(warning_levels) != "正常").sum()
	print(f"  -> {model_name} 诊断完成！")
	print(f"  -> 共诊断出 {total_anomalies} 个入流异常点。其中:")
	print(f"     - 轻度异常: {warning_levels.count('轻度异常')} 个")
	print(f"     - 中度异常: {warning_levels.count('中度异常')} 个")
	print(f"     - 重度异常: {warning_levels.count('重度异常')} 个")
	print(f"  -> 带标签诊断结果已导出至: {csv_path}")


# ================= 5. 模型构建与训练 =================
def build_and_train_lstm(X_train, y_train, config: Config):
	print("\n" + "=" * 50 + "\n阶段 3：训练 LSTM + Attention 干天基线模型\n" + "=" * 50)
	
	inputs = Input(shape=(X_train.shape[1], X_train.shape[2]))
	lstm1 = LSTM(units=config.lstm_units_1, return_sequences=True)(inputs)
	lstm1 = Dropout(rate=config.dropout_rate)(lstm1)
	lstm2 = LSTM(units=config.lstm_units_2, return_sequences=True)(lstm1)
	
	attention = Attention()([lstm2, lstm2])
	merged = Concatenate(axis=-1)([lstm2, attention])
	pooled = GlobalAveragePooling1D()(merged)
	outputs = Dense(units=config.predict_steps, activation='linear')(pooled)
	
	lstm_model = Model(inputs=inputs, outputs=outputs)
	lstm_model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=config.lstm_learning_rate), loss='mse')
	
	early_stopping = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)
	
	print("  -> 开始使用【仅含晴天】的数据进行训练...")
	lstm_model.fit(
		X_train, y_train,
		epochs=config.lstm_epochs,
		batch_size=config.lstm_batch_size,
		validation_split=0.2,
		callbacks=[early_stopping],
		verbose=1
	)
	
	lstm_model.save(os.path.join(config.model_dir, "lstm_baseline_model.h5"))
	return lstm_model


# ================= 主程序执行入口 =================
if __name__ == "__main__":
	config = Config()
	config.make_dirs()
	
	print("\n" + "=" * 50 + "\n阶段 1：数据集构建与干湿分离预处理\n" + "=" * 50)
	df = generate_mock_data(config)
	df_features = preprocess_data(config)
	
	feature_cols = ['Q', 'EC', 'time_sin', 'time_cos', 'peak_label', 'holiday_label']
	config.target_col_idx = 0
	
	scaler = StandardScaler()
	scaler.fit(df_features[feature_cols].values)
	joblib.dump(scaler, os.path.join(config.model_dir, "scaler.pkl"))
	
	print("\n" + "=" * 50 + "\n阶段 2：提取晴天数据训练，提取雨天数据测试\n" + "=" * 50)
	# 【新增解包】：接收计算出的干天基准电导率 ec_dry_baseline
	X_dry, y_dry, X_wet, y_wet, wet_dates, wet_ec, ec_dry_baseline = create_sequences_for_baseline(
		df_features, feature_cols, scaler, config
	)
	print(f"  -> 根据历史数据统计，计算出干天基准电导率 (EC_dry) 为: {ec_dry_baseline:.2f} μS/cm")
	print(f"  -> 成功隔离出 【晴天】训练样本: {len(X_dry)} 条")
	print(f"  -> 成功隔离出 【雨天】测试/诊断样本: {len(X_wet)} 条")
	
	# ================= 训练 Linear 模型 =================
	lr_model = LinearRegression()
	lr_model.fit(X_dry.reshape(X_dry.shape[0], -1), y_dry)
	evaluate_and_diagnose_rdii(X_wet, y_wet, wet_dates, wet_ec, ec_dry_baseline, lr_model, "Linear_Regression",
	                           feature_cols, scaler, config)
	
	# ================= 训练 RF 模型 =================
	rf_model = RandomForestRegressor(n_estimators=30, max_depth=10, random_state=42, n_jobs=-1)
	rf_model.fit(X_dry.reshape(X_dry.shape[0], -1), y_dry)
	evaluate_and_diagnose_rdii(X_wet, y_wet, wet_dates, wet_ec, ec_dry_baseline, rf_model, "Random_Forest",
	                           feature_cols, scaler, config)
	
	# ================= 训练 LSTM 模型 =================
	lstm_model = build_and_train_lstm(X_dry, y_dry, config)
	evaluate_and_diagnose_rdii(X_wet, y_wet, wet_dates, wet_ec, ec_dry_baseline, lstm_model, "LSTM_Attention",
	                           feature_cols, scaler, config)
	
	print("\n================ 全部流程执行完毕 ================")
	print(f"1. 完整的特征数据集保存在: {config.processed_data_path}")
	print(f"2. 最终的入流诊断结果保存在: {config.result_dir} 目录下。")