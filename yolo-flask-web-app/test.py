import cv2
from ultralytics import YOLO

# 1. 加载 YOLO 模型
model = YOLO(r"E:\PY\YOLO\yolov12\runs\egg3\weights\best.pt")  # 或者你自己训练的模型，如 "runs/train/egg_best.pt"

# 2. 打开视频文件
video_path = r"E:\chicken\20251020_154426.mp4"
cap = cv2.VideoCapture(video_path)

# 3. 视频输出（可选）
fps = cap.get(cv2.CAP_PROP_FPS)
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
out = cv2.VideoWriter(r"E:\PY\YOLO\yolov12\20251020_154426.mp4", cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

# 4. 去重计数变量
seen_ids = set()
total_count = 0

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    # 5. 执行追踪（ByteTrack 默认启用）
    results = model.track(frame, persist=True, tracker="bytetrack.yaml", conf=0.3)

    if results and len(results) > 0:
        boxes = results[0].boxes
        ids = boxes.id if hasattr(boxes, "id") else None

        # 遍历每个目标
        if ids is not None:
            for i, box_id in enumerate(ids):
                if box_id is None:
                    continue
                egg_id = int(box_id)
                if egg_id not in seen_ids:
                    seen_ids.add(egg_id)
                    total_count += 1

        # 6. 绘制带跟踪结果的帧
        annotated_frame = results[0].plot()

        # 显示计数
        cv2.putText(annotated_frame, f"Total Eggs: {total_count}", (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    else:
        annotated_frame = frame

    # 显示结果窗口
    cv2.imshow("Egg Tracking & Counting", annotated_frame)
    out.write(annotated_frame)

    # 按 Q 退出
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# 7. 释放资源
cap.release()
out.release()
cv2.destroyAllWindows()

print(f"视频处理完成，总计数：{total_count}")
