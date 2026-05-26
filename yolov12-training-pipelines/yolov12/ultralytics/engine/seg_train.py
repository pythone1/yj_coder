from ultralytics import YOLO
def main():
    """
    使用YOLOv8进行语义分割训练的主函数
    """
    # 1. 加载预训练的YOLOv8分割模型
    # 'yolov8n-seg.pt' 是一个轻量级的预训练分割模型，适合快速开始。
    # 其他选项包括 'yolov8s-seg.pt', 'yolov8m-seg.pt', 'yolov8l-seg.pt', 'yolov8x-seg.pt'
    model = YOLO('yolov8n-seg.pt')
    # 2. 开始训练
    # model.train() 方法会接收一系列参数来配置训练过程
    results = model.train(
        data=r'F:\data\sample\data.yaml',  # 数据集配置文件的路径
        epochs=20,                        # 训练轮次
        imgsz=512,                        # 训练图像尺寸
        batch=4,                          # 批次大小
        device='0',                       # 使用的设备，'0' 表示第一个GPU，'cpu' 表示CPU
        name='yolo_seg_experiment',       # 实验名称，结果会保存在 runs/segment/yolo_seg_experiment
        # 以下是一些可选但有用的参数
        # patience=50,                     # 早停耐心值，如果50个epoch验证集损失不下降就停止
        # save=True,                       # 保存训练过程中的模型
        # plots=True,                      # 生成训练曲线图
        # verbose=True,                    # 打印详细的训练日志
    )
    # 3. 训练完成后，可以评估模型在验证集上的性能
    print("\n训练完成，开始在验证集上评估...")
    metrics = model.val()
    # 4. （可选）使用训练好的模型进行推理
    # model.predict('path/to/your/test/image.jpg', save=True, imgsz=512)
if __name__ == '__main__':
    main()