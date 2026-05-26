"""
项目名称: yolov12-object-detection
技术领域: 02-computer-vision
模块说明: utils.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

# Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license


def adjust_bboxes_to_image_border(boxes, image_shape, threshold=20):
    """
    Adjust bounding boxes to stick to image border if they are within a certain threshold.

    Args:
        boxes (torch.Tensor): (n, 4)
        image_shape (tuple): (height, width)
        threshold (int): pixel threshold

    Returns:
        adjusted_boxes (torch.Tensor): adjusted bounding boxes
    """
    # Image dimensions
    h, w = image_shape

    # Adjust boxes
    boxes[boxes[:, 0] < threshold, 0] = 0  # x1
    boxes[boxes[:, 1] < threshold, 1] = 0  # y1
    boxes[boxes[:, 2] > w - threshold, 2] = w  # x2
    boxes[boxes[:, 3] > h - threshold, 3] = h  # y2
    return boxes
