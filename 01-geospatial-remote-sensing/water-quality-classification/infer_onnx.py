"""
项目名称: water-quality-classification
技术领域: 01-geospatial-remote-sensing
模块说明: infer_onnx.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

import os
import cv2
import numpy as np
import paddle
import onnxruntime as rt
print(rt.__version__)


def postprocess(results,with_postprocess=False):
    if with_postprocess:
        # 去除小的连通区域
        def remove_small_regions(seg_map, min_size=100):
            # 输入分割图像和最小的区域大小
            # 输出去除小连通区域后的分割图像
            # 使用OpenCV的连通组件分析来识别各个连通区域
            num, labels, stats, centroids = cv2.connectedComponentsWithStats(seg_map.astype(np.uint8), connectivity=8)
            # 去除小区域
            # print(num, labels, stats, centroids)
            for i in range(1, num):
                # print(stats[i, cv2.CC_STAT_AREA])
                if stats[i, cv2.CC_STAT_AREA] < min_size:
                    seg_map[labels == i] = 0
            return seg_map

        # 进行形态学操作
        def morphology_operation(seg_map, operation_type='close', kernel_size=5):
            # 输入分割图像，形态学操作类型和核大小
            # 输出进行形态学操作后的分割图像
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
            if operation_type == 'dilate':  # 膨胀
                seg_map = cv2.dilate(seg_map, kernel, iterations=1)
            elif operation_type == 'erode':  # 腐蚀
                seg_map = cv2.erode(seg_map, kernel, iterations=1)
            elif operation_type == 'open':  # 开运算 开运算可以去除小的噪声和细节，同时保留大的物体和整体结构
                seg_map = cv2.morphologyEx(seg_map, cv2.MORPH_OPEN, kernel)
            elif operation_type == 'close':  # 闭运算 闭运算可以填补小的空洞和断裂，同时保留大的物体和整体结构
                seg_map = cv2.morphologyEx(seg_map, cv2.MORPH_CLOSE, kernel)
            return seg_map

        # 进行后处理滤波
        def postprocess_filter(seg_map, filter_type='median', kernel_size=5):
            # 输入分割图像，滤波类型和核大小
            # 输出进行后处理滤波后的分割图像
            if filter_type == 'median':
                seg_map = cv2.medianBlur(seg_map.astype(np.uint8), kernel_size)
            elif filter_type == 'gaussian':
                seg_map = cv2.GaussianBlur(seg_map.astype(np.uint8), (kernel_size, kernel_size), 0)
            return seg_map

        # 进行后处理插值
        def postprocess_interpolation(seg_map, original_image_size):
            # 输入分割图像和原始图像尺寸
            # 输出插值后的分割图像
            resized_seg_map = cv2.resize(seg_map, original_image_size, interpolation=cv2.INTER_CUBIC)
            return resized_seg_map

        img = cv2.convertScaleAbs(results)
        # 二值化处理
        _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        # 开闭运算
        seg_map = morphology_operation(thresh, operation_type='erode', kernel_size=30)
        # seg_map = morphology_operation(thresh, operation_type='open', kernel_size=40)
        # # 去除小连通区域
        seg_map = remove_small_regions(seg_map, min_size=100)
        seg_map = postprocess_filter(seg_map, filter_type='median', kernel_size=5)

        return seg_map
    else:
        return results

def load_model(model_path):
    sess = rt.InferenceSession(model_path,providers=['CUDAExecutionProvider'])  # 创建ONNX Runtime的推理会话
    print(sess.get_providers())
    return sess

def preprocess(im):
    # 数据预处理，包括读取图像、转换颜色空间、标准化、转换维度等
    def normalize(im, mean, std):
        mean = np.array(mean)[np.newaxis, np.newaxis, :]
        std = np.array(std)[np.newaxis, np.newaxis, :]
        im = im.astype(np.float32, copy=False) / 255.0
        im -= mean
        im /= std
        im = np.transpose(im, (2, 0, 1))
        return im

    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)  # 转换为RGB颜色空间
    data = normalize(im, [0.5, 0.5, 0.5], [0.5, 0.5, 0.5])  # 标准化
    data = np.expand_dims(data, axis=0)  # 转换维度，将单张图像转换为形状为(1, C, H, W)的数组
    return data


def save_imgs(results, imgs_path, prefix=None):
    # 将模型的输出结果保存为图像文件
    for i in range(results.shape[0]):
        result = get_pseudo_color_map(results[i])  # 获取伪彩色图像
        # print(result)
        basename = os.path.basename(imgs_path)
        basename, _ = os.path.splitext(basename)
        if prefix is not None and isinstance(prefix, str):
            basename = prefix + "_" + basename
        basename = f'{basename}.png'
        result.save(os.path.join(save_dir, basename))  # 保存伪彩色图像

def get_pseudo_color_map(pred, color_map=None):
    # 将模型的输出结果转换为伪彩色图像
    from PIL import Image as PILImage
    pred_mask = PILImage.fromarray(pred.astype(np.uint8), mode='P')  # 创建PIL Image对象并设置数据和模式
    if color_map is None:
        color_map = get_color_map_list(256)  # 获取伪彩色映射表
    pred_mask.putpalette(color_map)  # 设置PIL Image对象的调色板
    return pred_mask

def get_color_map_list(num_classes, custom_color=None):
    # 获取伪彩色映射表
    num_classes += 1
    color_map = num_classes * [0, 0, 0]
    for i in range(0, num_classes):
        j = 0
        lab = i
        while lab:
            color_map[i * 3] |= (((lab >> 0) & 1) << (7 - j))
            color_map[i * 3 + 1] |= (((lab >> 1) & 1) << (7 - j))
            color_map[i * 3 + 2] |= (((lab >> 2) & 1) << (7 - j))
            j += 1
            lab >>= 3
    color_map = color_map[3:]

    if custom_color:
        color_map[:len(custom_color)] = custom_color
    return color_map

def paddle_predict(model_path,imgs_path):
    # 使用PaddlePaddle推理引擎运行模型
    model = paddle.jit.load(model_path)  # 加载模型
    model.eval()  # 切换到评估模式
    data = preprocess(imgs_path)  # 对输入图像进行预处理
    results = model(data).numpy()  # 使用模型进行推理，并将输出转换为NumPy数组
    results = postprocess(results)  # 对输出结果进行后处理，如使用 argmax 函数获取最终的预测结果
    return results

def onnx_predict(sess,im):
    # 使用ONNX Runtime推理引擎运行模型
    # sess = load_model(model_path)
    # print('模型记载完成')
    print(2)
    data = preprocess(im)  # 对输入图像进行预处理,im需要是float32
    print('数据预处理完成')
    results = sess.run(None, {sess.get_inputs()[0].name: data})[0]  # 使用模型进行推理
    print(results.shape)
    # 将其转换为 (2048, 2048) 的矩阵
    results = np.transpose(results, (1, 2, 0))
    print(results.shape)
    row,col,_ = results.shape
    results = results.reshape(row, col)
    print(type(results))
    print('预测完成')
    results = postprocess(results)  # 对输出结果进行后处理，如使用 argmax 函数获取最终的预测结果
    print('后处理完成')
    return results

if __name__ == '__main__':
    model_path = r"I:\pyMethod\ONNX_predict\2023_3_3_9_33_57_onnxmodel.onnx"
    image_path = r"I:\pyMethod\ONNX_predict\AC_14_7.png"
    use_paddle_predict = False
    save_dir = r"I:\pyMethod\ONNX_predict"
    with_postprocess = True

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    im = cv2.imread(image_path).astype('float32')
    if use_paddle_predict:
        paddle_result = paddle_predict(model_path,im)
        save_imgs(paddle_result, image_path, "paddle")
    else:
        onnx_result = onnx_predict(model_path,im)
        cv2.imwrite(r'D:\Desktop\test\vent\Reprojectfile\9.png',onnx_result)
        #RGB可视化
        # save_imgs(onnx_result, image_path, "onnx")
    print("预测完成")