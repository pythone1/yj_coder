from ultralytics import YOLO

if __name__ == "__main__":
  model = YOLO(r"E:\PY\YOLO\yolov12\yolov12x.pt")
  # 开始训练
  model.train(
    data=r"E:\PY\YOLO\yolov12\datasets\egg\data.yaml",  # 数据集配置文件
    epochs=20,  # 训练轮数a
    workers=2,
    imgsz=640,  # 输入图片大小
    batch=1,  # 批次
    device=0,  # GPU 0
    project="runs",  # 输出文件夹
    name="egg"  # 实验名称
    
  )



