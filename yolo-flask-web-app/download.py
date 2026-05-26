import os
import requests
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s - %(levelname)s - %(message)s',
	handlers=[
		logging.FileHandler('download_images.log', encoding='utf-8'),
		logging.StreamHandler()
	]
)

# 图片数据按主题分类
image_data = {
	"监控控制界面": [
![image]("https://sfile.chatglm.cn/image/4b/4ba7cae3.jpg)",
![image]("https://sfile.chatglm.cn/image/c7/c798ffe2.jpg)",
![image]("https://sfile.chatglm.cn/image/20/20e1a314.jpg)",
![image]("https://sfile.chatglm.cn/image/b7/b7f5b922.jpg)",
![image]("https://sfile.chatglm.cn/image/dc/dc1ad2c8.jpg)",
![image]("https://sfile.chatglm.cn/image/5d/5da4fae5.jpg)"
],
"数据分析平台": [
![image]("https://sfile.chatglm.cn/image/99/99bae91d.jpg)",
![image]("https://sfile.chatglm.cn/image/2b/2b602ca1.jpg)",
![image]("https://sfile.chatglm.cn/image/bf/bf3e44d8.jpg)",
![image]("https://sfile.chatglm.cn/image/9e/9e95e2eb.jpg)"
],
"AI算法与机器学习": [
![image]("https://sfile.chatglm.cn/image/9e/9ea4995f.jpg)",
![image]("https://sfile.chatglm.cn/image/91/91f3e670.jpg)",
![image]("https://sfile.chatglm.cn/image/3b/3b6f52d4.jpg)",
![image]("https://sfile.chatglm.cn/image/d3/d306f360.jpg)",
![image]("https://sfile.chatglm.cn/image/00/0082d598.jpg)",
![image]("https://sfile.chatglm.cn/image/f9/f9068966.jpg)",
![image]("https://sfile.chatglm.cn/image/7d/7dead648.jpg)",
![image]("https://sfile.chatglm.cn/image/44/440ae623.jpg)",
![image]("https://sfile.chatglm.cn/image/3d/3dc425e7.jpg)"
],
"水质监测与环境控制": [
![image]("https://sfile.chatglm.cn/image/1c/1cb7bf1e.jpg)",
![image]("https://sfile.chatglm.cn/image/5e/5e9e89ed.jpg)",
![image]("https://sfile.chatglm.cn/image/01/01a631a1.jpg)",
![image]("https://sfile.chatglm.cn/image/cd/cd2139f1.jpg)",
![image]("https://sfile.chatglm.cn/image/73/7316761a.jpg)",
![image]("https://sfile.chatglm.cn/image/68/682371a6.jpg)"
],
"智能投饵系统": [
![image]("https://sfile.chatglm.cn/image/ee/eeb73314.jpg)",
![image]("https://sfile.chatglm.cn/image/56/56d04478.jpg)",
![image]("https://sfile.chatglm.cn/image/d9/d98e8dc9.jpg)",
![image]("https://sfile.chatglm.cn/image/24/24551eb7.jpg)"
],
"质量检测与食品安全": [
![image]("https://sfile.chatglm.cn/image/c1/c1e32c5f.jpg)",
![image]("https://sfile.chatglm.cn/image/8f/8f3b9b0.jpg)",
![image]("https://sfile.chatglm.cn/image/42/4287135b.jpg)",
![image]("https://sfile.chatglm.cn/image/15/1513d565.jpg)",
![image]("https://sfile.chatglm.cn/image/a5/a585163a.jpg)"
],
"循环水养殖系统": [
![image]("https://sfile.chatglm.cn/image/64/6428cd90.jpg)",
![image]("https://sfile.chatglm.cn/image/0d/0d9031b6.jpg)",
![image]("https://sfile.chatglm.cn/image/be/be9b7f95.jpg)",
![image]("https://sfile.chatglm.cn/image/43/43edf55a.jpg)",
![image]("https://sfile.chatglm.cn/image/89/89460324.jpg)"
],
"淡水养殖场景": [
![image]("https://sfile.chatglm.cn/image/63/63b4ef22.jpg)",
![image]("https://sfile.chatglm.cn/image/79/79fee3b4.jpg)",
![image]("https://sfile.chatglm.cn/image/e2/e2c7f885.jpg)",
![image]("https://sfile.chatglm.cn/image/7c/7c55f7d8.jpg)"
],
"智能设备与传感器": [
![image]("https://sfile.chatglm.cn/image/05/055fe0d5.jpg)",
![image]("https://sfile.chatglm.cn/image/90/9014b25d.jpg)",
![image]("https://sfile.chatglm.cn/image/c3/c354ac4b.jpg)"
]
}

def download_image(url, save_path, timeout=30):
	"""下载单个图片"""
	try:
		response = requests.get(url, timeout=timeout)
		response.raise_for_status()
		
		with open(save_path, 'wb') as f:
			f.write(response.content)
		return True
	except requests.RequestException as e:
		logging.error(f"下载失败 {url}: {str(e)}")
		return False


def main():
	# 获取当前工作目录
	base_dir = Path.cwd()
	
	# 创建主文件夹
	main_folder = base_dir / "淡水养殖图片资源"
	main_folder.mkdir(exist_ok=True)
	logging.info(f"主文件夹已创建: {main_folder}")
	
	total_images = 0
	total_downloaded = 0
	
	# 遍历每个主题
	for subject, urls in image_data.items():
		# 创建主题子文件夹
		subject_folder = main_folder / subject
		subject_folder.mkdir(exist_ok=True)
		
		total_images += len(urls)
		
		logging.info(f"\n开始处理主题: {subject} (共 {len(urls)} 张图片)")
		
		# 下载该主题下的所有图片
		for idx, url in enumerate(urls, 1):
			# 生成文件名 (按顺序重命名)
			file_extension = url.split('.')[-1]
			file_name = f"{idx:02d}.{file_extension}"
			save_path = subject_folder / file_name
			
			# 显示进度
			logging.info(f"  [{idx}/{len(urls)}] 正在下载: {file_name}")
			
			# 下载图片
			if download_image(url, save_path):
				total_downloaded += 1
				logging.info(f"    ✓ 下载成功")
			else:
				logging.warning(f"    ✗ 下载失败")
	
	# 输出总结
	logging.info("\n" + "=" * 50)
	logging.info("下载完成!")
	logging.info(f"总计: {total_images} 张图片")
	logging.info(f"成功: {total_downloaded} 张")
	logging.info(f"失败: {total_images - total_downloaded} 张")
	logging.info(f"保存位置: {main_folder}")
	logging.info("=" * 50)


if __name__ == "__main__":
	main()