"""
项目名称: yolov12-object-detection
技术领域: 02-computer-vision
模块说明: .py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

import cv2
import os
import glob


# 输入视频目录
VIDEO_DIR = r"E:\chicken"
# 输出图片目录
OUTPUT_DIR = r"E:\chicken\dataset"
# 每隔多少秒取一帧
INTERVAL = 60

def extract_frames_from_videos():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    video_files = glob.glob(os.path.join(VIDEO_DIR, "*.mp4")) \
                + glob.glob(os.path.join(VIDEO_DIR, "*.avi")) \
                + glob.glob(os.path.join(VIDEO_DIR, "*.mov")) \
                + glob.glob(os.path.join(VIDEO_DIR, "*.mkv"))

    if not video_files:
        print("未找到视频文件，请检查 VIDEO_DIR 路径")
        return

    for video_path in video_files:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"无法打开视频: {video_path}")
            continue

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0:
            print(f"无法获取FPS: {video_path}")
            continue

        interval_frames = int(fps * INTERVAL)
        basename = os.path.splitext(os.path.basename(video_path))[0]

        frame_count = 0
        save_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % interval_frames == 0:
                out_path = os.path.join(OUTPUT_DIR, f"{basename}_frame{save_count:05d}.jpg")
                cv2.imwrite(out_path, frame)
                save_count += 1

            frame_count += 1

        cap.release()
        print(f"{video_path} 拆帧完成，共保存 {save_count} 张图片")

if __name__ == "__main__":
    extract_frames_from_videos()
