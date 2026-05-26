import requests
import pandas as pd
import json
import time
import threading
import http.server
import socketserver
import os
import random

STOCK_CODE = "hk02513"
DATA_FILE = "zhipu_data.json"


def calculate_daily_indicators(df):
	if df.empty: return df
	for col in ['open', 'close', 'high', 'low', 'vol']:
		df[col] = pd.to_numeric(df[col], errors='coerce')
	df['MA5'] = df['close'].rolling(window=5, min_periods=1).mean()
	df['MA20'] = df['close'].rolling(window=20, min_periods=1).mean()
	df['STD20'] = df['close'].rolling(window=20, min_periods=2).std().fillna(0)
	df['UPPER'] = df['MA20'] + 2 * df['STD20']
	df['LOWER'] = df['MA20'] - 2 * df['STD20']
	exp1 = df['close'].ewm(span=12, adjust=False).mean()
	exp2 = df['close'].ewm(span=26, adjust=False).mean()
	df['DIF'] = exp1 - exp2
	df['DEA'] = df['DIF'].ewm(span=9, adjust=False).mean()
	df['MACD'] = (df['DIF'] - df['DEA']) * 2
	return df.fillna(0)


def fetch_and_save_data():
	print("⏳ [V2.6] 全字段实时监控引擎启动...")
	while True:
		try:
			# 1. 获取毫秒级实时盘口
			# 腾讯接口: 3:现价, 4:昨收, 5:开盘, 32:涨跌%, 33:最高, 34:最低
			rt_res = requests.get(f"http://qt.gtimg.cn/q={STOCK_CODE}", timeout=2).text
			rt_arr = rt_res.split('"')[1].split('~')
			
			price = float(rt_arr[3])  # 现价
			prev_close = float(rt_arr[4])
			open_price = float(rt_arr[5])  # 开盘价
			high_price = float(rt_arr[33])
			low_price = float(rt_arr[34])
			
			# 2. 获取分时数据
			min_url = f"http://web.ifzq.gtimg.cn/appstock/app/minute/query?code={STOCK_CODE}"
			min_res = requests.get(min_url, timeout=3).json()
			min_data_raw = min_res['data'][STOCK_CODE]['data']['data']
			
			intraday_times, intraday_prices, intraday_vols, intraday_vwaps = [], [], [], []
			total_vol, total_amount = 0, 0
			
			for row in min_data_raw:
				parts = row.split(' ')
				if len(parts) >= 3:
					t_str = parts[0]
					intraday_times.append(f"{t_str[:2]}:{t_str[2:]}")
					p, v = float(parts[1]), float(parts[2])
					intraday_prices.append(p)
					intraday_vols.append(v)
					total_vol += v
					total_amount += p * v
					intraday_vwaps.append(round(total_amount / total_vol if total_vol > 0 else p, 2))
			
			# 分时指标计算
			df_min = pd.DataFrame({'price': intraday_prices, 'vol': intraday_vols})
			df_min['prev_price'] = df_min['price'].shift(1).fillna(prev_close)
			df_min['net_vol'] = df_min.apply(lambda r: r['vol'] if r['price'] >= r['prev_price'] else -r['vol'], axis=1)
			
			df_min['MA20'] = df_min['price'].rolling(window=20, min_periods=1).mean()
			df_min['STD20'] = df_min['price'].rolling(window=20, min_periods=2).std().fillna(0)
			df_min['UPPER'] = df_min['MA20'] + 2 * df_min['STD20']
			df_min['LOWER'] = df_min['MA20'] - 2 * df_min['STD20']
			
			e1 = df_min['price'].ewm(span=12, adjust=False).mean()
			e2 = df_min['price'].ewm(span=26, adjust=False).mean()
			df_min['DIF'] = e1 - e2
			df_min['DEA'] = df_min['DIF'].ewm(span=9, adjust=False).mean()
			df_min['MACD'] = (df_min['DIF'] - df_min['DEA']) * 2
			df_min = df_min.fillna(0)
			
			# 3. 日线数据
			kline_url = f"http://web.ifzq.gtimg.cn/appstock/app/hkfqkline/get?param={STOCK_CODE},day,,,60,qfq"
			kline_res = requests.get(kline_url, timeout=5).json()
			kline_raw = kline_res['data'][STOCK_CODE].get('qfqday', kline_res['data'][STOCK_CODE].get('day', []))
			kline_raw = [row[:6] for row in kline_raw]
			
			df_day = pd.DataFrame(kline_raw, columns=['date', 'open', 'close', 'high', 'low', 'vol'])
			df_day = calculate_daily_indicators(df_day)
			df_day['prev_close'] = df_day['close'].shift(1).fillna(df_day['open'])
			df_day['net_vol'] = df_day.apply(lambda r: r['vol'] if r['close'] >= r['open'] else -r['vol'], axis=1)
			df_recent = df_day.tail(60)
			
			# 4. 盘口解析
			def safe_float(val):
				try:
					return float(val)
				except:
					return 0.0
			
			bids = [[safe_float(rt_arr[i]), safe_float(rt_arr[i + 1])] for i in range(9, 18, 2)]
			asks = [[safe_float(rt_arr[i]), safe_float(rt_arr[i + 1])] for i in range(19, 28, 2)]
			
			# 5. 实时量化信号 (强制刷新)
			vwap_now = intraday_vwaps[-1] if intraday_vwaps else price
			macd_val = df_day.iloc[-1]['MACD']
			
			final_data = {
				"realtime": {
					"price": price, "prev_close": prev_close, "open": open_price,
					"high": high_price, "low": low_price, "change_pct": float(rt_arr[32]),
					"vol": float(rt_arr[36]), "turnover": float(rt_arr[37]), "time": time.strftime("%H:%M:%S")
				},
				"order_book": {"bids": bids, "asks": asks},
				"intraday": {
					"times": intraday_times, "prices": intraday_prices, "vwaps": intraday_vwaps,
					"net_vols": df_min['net_vol'].tolist(),
					"upper": df_min['UPPER'].round(2).tolist(), "lower": df_min['LOWER'].round(2).tolist(),
					"macd": df_min['MACD'].round(3).tolist(), "dif": df_min['DIF'].round(3).tolist(),
					"dea": df_min['DEA'].round(3).tolist()
				},
				"kline": {
					"dates": df_recent['date'].astype(str).tolist(),
					"values": df_recent[['open', 'close', 'low', 'high']].values.tolist(),
					"net_vols": df_recent['net_vol'].tolist(),
					"ma5": df_recent['MA5'].round(2).tolist(), "ma20": df_recent['MA20'].round(2).tolist(),
					"macd": df_recent['MACD'].round(3).tolist(), "dif": df_recent['DIF'].round(3).tolist(),
					"dea": df_recent['DEA'].round(3).tolist()
				},
				"quant_signals": {
					"update_time": time.strftime("%H:%M:%S"),
					"intraday_trend": "强势 (均线上方)" if price >= vwap_now else "弱势 (均线下方)",
					"macd_signal": "金叉共振 (强)" if macd_val > 0 else "死叉调整 (弱)",
					"boll_signal": "触及上轨 (超买)" if price >= df_day.iloc[-1]['UPPER'] else (
						"触及下轨 (超卖)" if price <= df_day.iloc[-1]['LOWER'] else "中轨运行"),
					"advice": "持股待涨 / 逢低买入" if price > vwap_now and macd_val > 0 else "谨慎观望 / 高抛低吸"
				}
			}
			
			with open(DATA_FILE, "w", encoding="utf-8") as f:
				json.dump(final_data, f, ensure_ascii=False)
			
			print(f"[{time.strftime('%H:%M:%S')}] ✅ 现价:{price} | 开盘:{open_price} | 状态:写入成功")
		
		except Exception as e:
			print(f"❌ 异常: {e}")
		
		time.sleep(2)


def start_local_server():
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	Handler = http.server.SimpleHTTPRequestHandler
	with socketserver.TCPServer(("", 8888), Handler) as httpd:
		print("\n" + "=" * 50)
		print("🌐 [V2.6] 终端服务器启动")
		print("👉 访问: http://127.0.0.1:8888")
		print("=" * 50 + "\n")
		httpd.serve_forever()


if __name__ == "__main__":
	threading.Thread(target=fetch_and_save_data, daemon=True).start()
	start_local_server()