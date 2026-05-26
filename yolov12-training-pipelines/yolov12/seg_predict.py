import os
from pathlib import Path
import cv2
import numpy as np
import json
from tqdm import tqdm
from ultralytics import YOLO
import argparse


def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def mask_to_uint8(mask_bool):
    """bool mask 转 uint8 0/255"""
    return (mask_bool.astype(np.uint8) * 255)


def masks_tensor_to_numpy(masks_obj):
    """兼容 YOLO masks 转 numpy"""
    masks = []
    if masks_obj is None:
        return masks
    if hasattr(masks_obj, 'data') and masks_obj.data is not None:
        arr = masks_obj.data
        try:
            np_arr = arr.cpu().numpy()
        except Exception:
            np_arr = np.array(arr)
        for i in range(np_arr.shape[0]):
            m = np_arr[i] > 0.5
            masks.append(m.astype(bool))
    elif hasattr(masks_obj, 'masks') and masks_obj.masks is not None:
        arr = masks_obj.masks
        try:
            np_arr = arr.cpu().numpy()
        except Exception:
            np_arr = np.array(arr)
        for i in range(np_arr.shape[0]):
            m = np_arr[i] > 0.5
            masks.append(m.astype(bool))
    return masks


def visualize_and_save(image, boxes, scores, cls_ids, class_names, masks, save_path):
    """绘制检测结果"""
    vis = image.copy()
    overlay = image.copy()

    for i, m in enumerate(masks):
        color = np.random.randint(0, 255, size=3).tolist()
        overlay[m] = overlay[m] * 0.5 + np.array(color) * 0.5

    vis = cv2.addWeighted(overlay, 0.8, vis, 0.2, 0)

    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = [int(v) for v in box]
        cls = int(cls_ids[i])
        label = f"{class_names[cls]} {scores[i]:.2f}"
        cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(vis, label, (x1, max(15, y1 - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.imwrite(save_path, vis)


def main(args):
    # 路径准备
    model_path = Path(args.model)
    source_dir = Path(args.source)
    output_dir = Path(args.out_dir)
    ensure_dir(output_dir)
    ensure_dir(output_dir / "vis")
    ensure_dir(output_dir / "masks")

    # 加载模型
    model = YOLO(model_path)

    # 获取图片列表
    img_list = [p for p in source_dir.glob("*") if p.suffix.lower() in [
        ".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"]]
    print(f"共检测到 {len(img_list)} 张图片")

    for img_path in tqdm(img_list, desc="预测中"):
        img = cv2.imread(str(img_path))
        if img is None:
            print("读取失败:", img_path)
            continue
        H, W = img.shape[:2]

        # 推理
        results = model.predict(
            str(img_path),
            imgsz=args.imgsz,
            conf=args.conf,
            iou=args.iou,
            device=args.device,
            verbose=False
        )
        r = results[0]

        boxes = r.boxes.xyxy.cpu().numpy() if r.boxes is not None else []
        scores = r.boxes.conf.cpu().numpy() if r.boxes is not None else []
        cls_ids = r.boxes.cls.cpu().numpy().astype(int) if r.boxes is not None else []
        masks = masks_tensor_to_numpy(r.masks)
        class_names = model.names

        base = img_path.stem

        # 保存mask
        for i, m in enumerate(masks):
            mask_path = output_dir / "masks" / f"{base}_mask_{i}.png"
            cv2.imwrite(str(mask_path), mask_to_uint8(m))

        # 保存可视化
        vis_path = output_dir / "vis" / f"{base}_vis.png"
        visualize_and_save(img, boxes, scores, cls_ids,
                           class_names, masks, str(vis_path))

        # 保存 JSON 结果
        json_path = output_dir / f"{base}.json"
        dets = []
        for i in range(len(boxes)):
            dets.append({
                "bbox": [float(v) for v in boxes[i]],
                "score": float(scores[i]),
                "class_id": int(cls_ids[i]),
                "class_name": class_names[int(cls_ids[i])] if class_names else None
            })
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({"image": img_path.name, "detections": dets},
                      f, ensure_ascii=False, indent=2)

    print("✅ 预测完成，结果保存在：", r'F:\data\sample\test\result')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="图像分割预测脚本")

    parser.add_argument(
        "--model",
        type=str,
        default=r"F:\data\sample\yolov8n-seg.pt",
        help="模型文件路径（.pt）"
    )
    parser.add_argument(
        "--source",
        type=str,
        default=r"F:\data\test\test",
        help="输入图片文件夹路径"
    )
    parser.add_argument(
        "--out_dir",
        type=str,
        default=r"F:\data\sample\results",
        help="输出结果文件夹路径"
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=1024,
        help="输入图像尺寸（默认640）"
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="置信度阈值"
    )
    parser.add_argument(
        "--iou",
        type=float,
        default=0.45,
        help="NMS IoU 阈值"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="0",
        help="推理设备，如 '0'、'cpu'"
    )

    args = parser.parse_args()
    main(args)
