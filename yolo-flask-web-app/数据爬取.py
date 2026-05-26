import requests
import pandas as pd
import akshare as ak
import time
import os
import ctypes
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# --- 配置区 ---
STOCK_CODE_RT = "hk02513"
STOCK_CODE_HIST = "02513"
REFRESH_RATE = 10  # 壁纸刷新频率（秒）
SCREEN_WIDTH = 1920  # 你的屏幕分辨率宽度
SCREEN_HEIGHT = 1080  # 你的屏幕分辨率高度

# 历史数据缓存
hist_data_cache = None
last_hist_update = 0


def fetch_hist_data():
	"""获取历史数据并计算指标 (修复了新股天数不足的Bug)"""
	global hist_data_cache, last_hist_update
	if time.time() - last_hist_update > 3600 or hist_data_cache is None:
		try:
			print("正在拉取历史K线进行量化计算...")
			df = ak.stock_hk_daily(symbol=STOCK_CODE_HIST, adjust="qfq")
			
			# 【修复点1】不再限制 len(df) > 30。只要有数据就计算。
			if df is not None and not df.empty:
				# 使用 min_periods=1 兼容新股（哪怕上市只有5天，也能强行计算均值）
				df['MA5'] = df['close'].rolling(window=5, min_periods=1).mean()
				df['MA20'] = df['close'].rolling(window=20, min_periods=1).mean()
				
				# RSI 计算 (14日)
				delta = df['close'].diff()
				gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
				loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
				rs = gain / loss
				df['RSI'] = 100 - (100 / (1 + rs))
				df['RSI'] = df['RSI'].fillna(50)  # 第一天没有波动时默认为50
				
				# 布林带计算
				df['std20'] = df['close'].rolling(window=20, min_periods=2).std()
				df['std20'] = df['std20'].fillna(0)  # 早期数据标准差可能为空
				df['upper_band'] = df['MA20'] + (df['std20'] * 2)
				df['lower_band'] = df['MA20'] - (df['std20'] * 2)
				
				hist_data_cache = df.iloc[-1]
				last_hist_update = time.time()
				print("✅ 历史量化数据拉取并计算成功！")
			else:
				print("⚠️ 未获取到历史数据，可能是 Akshare 接口延迟。")
		except Exception as e:
			print(f"❌ 历史数据获取失败: {e}")


def create_wallpaper(rt_data):
	"""生成带有数据的壁纸图片"""
	# 背景底色
	img = Image.new('RGB', (SCREEN_WIDTH, SCREEN_HEIGHT), color=(25, 25, 30))
	draw = ImageDraw.Draw(img)
	
	# 【修复点2】强制使用 Windows 绝对路径加载微软雅黑字体，防止中文消失
	font_path = "C:\\Windows\\Fonts\\msyh.ttc"
	try:
		font_huge = ImageFont.truetype(font_path, 80)
		font_large = ImageFont.truetype(font_path, 40)
		font_normal = ImageFont.truetype(font_path, 24)
		font_small = ImageFont.truetype(font_path, 18)
	except IOError:
		print("⚠️ 找不到微软雅黑字体，将使用系统默认备用字体！")
		font_huge = font_large = font_normal = font_small = ImageFont.load_default()
	
	# --- 实时数据解析 ---
	price = float(rt_data[6])
	change_pct = float(rt_data[8])
	update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	
	# 颜色判定 (涨红跌绿)
	color_main = (255, 80, 80) if change_pct > 0 else (80, 255, 80)
	sign = "+" if change_pct > 0 else ""
	
	# --- 绘制位置设定 (屏幕右侧) ---
	start_x = SCREEN_WIDTH - 650
	start_y = 150
	line_spacing = 45
	
	# 1. 绘制表头和实时价格
	draw.text((start_x, start_y), "智谱 (02513.HK) 实时量化看板", font=font_large, fill=(200, 200, 200))
	start_y += 80
	draw.text((start_x, start_y), f"{price:.2f} HKD", font=font_huge, fill=color_main)
	start_y += 100
	draw.text((start_x, start_y), f"涨跌幅: {sign}{change_pct}%", font=font_large, fill=color_main)
	start_y += 60
	draw.text((start_x, start_y), f"更新时间: {update_time}", font=font_small, fill=(120, 120, 120))
	start_y += 60
	
	# 分割线
	draw.line([(start_x, start_y), (start_x + 550, start_y)], fill=(100, 100, 100), width=2)
	start_y += 30
	
	# 2. 绘制量化分析指标 (只有在获取到数据时才会绘制)
	if hist_data_cache is not None:
		ma5 = hist_data_cache['MA5']
		ma20 = hist_data_cache['MA20']
		rsi = hist_data_cache['RSI']
		upper = hist_data_cache['upper_band']
		lower = hist_data_cache['lower_band']
		
		# 量化研判逻辑
		trend = "多头排列 (强势)" if price > ma5 > ma20 else "空头排列 (弱势)" if ma20 > ma5 > price else "震荡盘整"
		rsi_stat = "超买 (风险较高)" if rsi > 70 else "超卖 (反弹预期)" if rsi < 30 else "动能中性"
		band_stat = "突破上轨" if price > upper else "跌破下轨" if price < lower else "通道内运行"
		
		metrics = [
			("【趋势分析】", ""),
			(f"MA5 短期均线:", f"{ma5:.2f} HKD"),
			(f"MA20 中期均线:", f"{ma20:.2f} HKD"),
			(f"趋势研判:", trend),
			("【动能与空间】", ""),
			(f"RSI 强弱指标:", f"{rsi:.2f} ({rsi_stat})"),
			(f"布林带上轨 (压力):", f"{upper:.2f} HKD"),
			(f"布林带下轨 (支撑):", f"{lower:.2f} HKD"),
			(f"价格位置:", band_stat)
		]
		
		for label, val in metrics:
			if "【" in label:
				start_y += 10  # 分组间距
				draw.text((start_x, start_y), label, font=font_normal, fill=(255, 200, 0))
			else:
				# 绘制标签
				draw.text((start_x + 20, start_y), label, font=font_normal, fill=(180, 180, 180))
				
				# 绘制数值，重点高亮多空情绪
				val_color = (255, 255, 255)  # 默认白色
				if "强势" in val or "超卖" in val or "突破" in val: val_color = (255, 80, 80)  # 偏多头红色
				if "弱势" in val or "超买" in val or "跌破" in val: val_color = (80, 255, 80)  # 偏空头绿色
				
				draw.text((start_x + 300, start_y), val, font=font_normal, fill=val_color)
			
			start_y += line_spacing
	else:
		draw.text((start_x, start_y), "正在初始化量化分析数据，请稍后...", font=font_normal, fill=(150, 150, 150))
	
	# 保存图片到当前工作目录
	wallpaper_path = os.path.abspath("zhipu_quant_wallpaper.png")
	img.save(wallpaper_path)
	return wallpaper_path


def set_wallpaper(image_path):
	"""调用 Windows API 设置壁纸"""
	SPI_SETDESKWALLPAPER = 20
	ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, image_path, 3)


def main():
	print("🚀 动态壁纸引擎已启动！请退回桌面查看...")
	print("注: 因为是新股，前几次刷新时后台正在计算补全量化指标，请稍等10秒...")
	while True:
		try:
			# 1. 抓取实时数据
			rt_url = f"http://hq.sinajs.cn/list=rt_{STOCK_CODE_RT}"
			headers = {"Referer": "http://finance.sina.com.cn", "User-Agent": "Mozilla/5.0"}
			resp = requests.get(rt_url, headers=headers, timeout=5)
			rt_str = resp.text.split('"')[1]
			if not rt_str:
				continue
			rt_data = rt_str.split(',')
			
			# 2. 检查并更新历史量化数据
			fetch_hist_data()
			
			# 3. 绘制壁纸并设置
			img_path = create_wallpaper(rt_data)
			set_wallpaper(img_path)
			
			print(f"[{datetime.now().strftime('%H:%M:%S')}] 壁纸刷新成功 | 最新价: {rt_data[6]}")
		
		except Exception as e:
			print(f"[{datetime.now().strftime('%H:%M:%S')}] 刷新遇到波动: {e}")
		
		# 休息 10 秒
		time.sleep(REFRESH_RATE)


if __name__ == "__main__":
	main()