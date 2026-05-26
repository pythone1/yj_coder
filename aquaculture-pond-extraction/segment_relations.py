import time, os, glob

import numpy as np
import geopandas as gpd
import pandas as pd
import cv2
import torch
import matplotlib.pyplot as plt
import shapely
from shapely import wkt
from rasterio import features
from osgeo import gdal
from shapely.geometry import Polygon
from segment_anything import SamAutomaticMaskGenerator, sam_model_registry, SamPredictor

import imgProcess as imgpro

MODEL_PATH = r'D:\PY\segment-anything-main\sam_vit_h_4b8939.pth'
MODEL_TYPE = 'vit_h'
''' 或者在这里定义分割区域，或者在“池塘分割_分割及筛选d5m_整块1.py”脚本前面定义'''
# QX = '江苏省_南京市_栖霞区' 
# SAVEPATH = f'S:\\项目数据\\江苏省一池一档水产养殖基本情况普查项目\\图像分割\\分割结果\\{QX}'
# os.makedirs(SAVEPATH,exist_ok=True)  
# # 分割影像：天地图0.5米
# rgbpath = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\图像分割\准备数据\d5m天地图影像'
# _,ROWS,COLS,_ = imgpro.getGeoInfo(f'{rgbpath}\\{QX}.tif')
# HROWS = int(ROWS/6515/2)*6515
# HCOLS = int(COLS/6515/2)*6515

# SAM参数
SAM_ARGS = {
    'points_per_side': 32,
    'points_per_batch': 64,
    'pred_iou_thresh': 0.7,  # 低于0.7可用率不高
    'stability_score_thresh': 0.7,  # 低于0.7可用率不高
    'stability_score_offset': 1,
    'box_nms_thresh': 0.7,  # 需要抑制，减少输出图斑数量
    'crop_n_layers': 0,
    'crop_nms_thresh': 1,
    'crop_overlap_ratio': 512 / 1500,
    'crop_n_points_downscale_factor': 1,
    'point_grids': None,
    'min_mask_region_area': 0,
    'output_mode': "binary_mask",
}


def load_mask_generator(model_path=r'D:\PY\segment-anything-main\sam_vit_h_4b8939.pth', device_ids=[0],
                        model_type='vit_h', sam_args=None):
    '''
    加载模型到单gpu或多gpu：
    model_path: str 模型参数路径
    device_ids: list[int] 设备id的list
    model_type: str 模型类型,vit_h
    '''
    model = sam_model_registry[model_type](checkpoint=model_path) # 加载模型
    if len(device_ids) == 1:
        model.to(device=f"cuda:{device_ids[0]}")  # 将模型转移到设备（CPU或GPU）
    elif len(device_ids) > 1:
        model = torch.nn.DataParallel(model.cuda(), device_ids=device_ids)
        model = model.module
        model.eval()
    else:
        model.to(device="cpu")

    if sam_args is None:
        # 加载SAM自动分割模型
        mask_generator = SamAutomaticMaskGenerator(
            model=model,
            points_per_side=32,  # 每边点的数量，
            points_per_batch=64,
            pred_iou_thresh=0.5,
            stability_score_thresh=0.5,
            min_mask_region_area=200,
        )
    else:
        mask_generator = SamAutomaticMaskGenerator(
            model=model,
            points_per_side=sam_args['points_per_side'],
            points_per_batch=sam_args['points_per_batch'],
            pred_iou_thresh=sam_args['pred_iou_thresh'],
            stability_score_thresh=sam_args['stability_score_thresh'],
            stability_score_offset=sam_args['stability_score_offset'],
            box_nms_thresh=sam_args['box_nms_thresh'],
            crop_n_layers=sam_args['crop_n_layers'],
            crop_nms_thresh=sam_args['crop_nms_thresh'],
            crop_overlap_ratio=sam_args['crop_overlap_ratio'],
            crop_n_points_downscale_factor=sam_args['crop_n_points_downscale_factor'],
            point_grids=sam_args['point_grids'],
            min_mask_region_area=sam_args['min_mask_region_area'],
            output_mode=sam_args['output_mode'],
        )
    return mask_generator


def load_predictor(model_path=r'D:\PY\segment-anything-main\sam_vit_h_4b8939.pth', device_ids=[0], model_type='vit_h'):
    '''
    加载点提示的预测模型
    model_path: str 模型参数路径
    device_ids: list[int] 设备id的list
    model_type: str 模型类型,vit_h
    '''
    model = sam_model_registry[model_type](checkpoint=model_path) # 加载模型
    if len(device_ids) == 1:
        model.to(device=f"cuda:{device_ids[0]}")  # 将模型转移到设备（CPU或GPU）
    elif len(device_ids) > 1:
        model = torch.nn.DataParallel(model.cuda(), device_ids=device_ids)
        model = model.module
        model.eval()
    else:
        model.to(device="cpu")

    predictor = SamPredictor(model)

    return predictor

def load_data(imgfile, drange=None):
    '''
    加载数据
    imgfile: str 影像文件
    drange: list[int]，读取范围，None读取所有行列，否则用[xoff,yoff,xsize,ysize]指定读取范围
    xoff,yoff: int 起始行列号
    xsize,ysize: int 读取行列数
    '''
    geotif = imgpro.geotiffread(imgfile, drange)
    print(f'行：{geotif.rows}\n列：{geotif.cols}\n波段数：{geotif.bands}\n数据类型：{type(data[0, 0, 0])}')

    return geotif


def segment_by_windows(data, geotrans, mask_generator, w_size=512, w_step=256, k_size=3):
    '''
    按滑动窗口分割
    data: 待分割图像
    geotrans: 地理六参数
    mask_generator: SamAutomaticMaskGenerator 分割模型
    w_size: int 每次分割窗口大小
    w_step: int 分割窗口滑动步长
    k_szie: int 分割结果做形态处理的窗口大小
    '''
    morph_kernel = np.ones((k_size, k_size), np.uint8) # 形态处理核
    rows, cols = data.shape[0:2]
    x_size = geotrans[1]
    y_size = geotrans[5]
    results = {}
    # for k in ['segmentation','bbox','area','predicted_iou','point_coords','stability_score','crop_box']:
    #     results[k] = []
    for k in ['segmentation', 'predicted_iou', 'stability_score']:
        results[k] = []

    for i in range(0, rows, w_step): # 行方向滑动
        for j in range(0, cols, w_step): # 列方向滑动
            j = min(j, max(0, cols - w_size)) # 防止窗口超出右边界

            # 获取数据数组的子集（即分块）
            subset = data[i:i + w_size, j:j + w_size] # 获取子集数据
            st_x = geotrans[0] + geotrans[1] * j    # 计算子集左上角x坐标
            st_y = geotrans[3] + geotrans[5] * i    # 计算子集左上角y坐标

            # 如果子集中的最大值大于0（说明子集中有数据），则进行预测
            if np.max(subset) > 0:
                # 进行分割
                result = segment_single(subset, mask_generator, morph_kernel=morph_kernel, st_xy=[st_x, st_y],
                                        xy_size=[x_size, y_size], del_outsides=True)
                # 合并结果
                for k in list(results.keys()):
                    results[k].extend(result[k])

            if j + w_size >= cols: break
        if i + w_size >= rows: break
    return results


def segment_single(img, mask_generator, morph_kernel, st_xy=[0, 0], xy_size=[1, 1], del_outsides=False):
    '''
    图像分割（单次）
    img: np.darray 待分割图像
    mask_generator: SamAutomaticMaskGenerator
    morph_kernel: cv2形态处理的核
    st_xy: list[float] 用于坐标转换，左上角x（列方向），y（行方向）坐标
    xy_size: list[float] 用于坐标转换，x\y方向分辨率
    del_outsides:bool 是否删除图像边缘的轮廓
    '''
    masks = mask_generator.generate(img)  # 对子集进行预测，并获取预测结果（掩膜）

    return masks2features(masks, st_xy, xy_size, del_outsides=del_outsides, morph_kernel=morph_kernel)


def masks2features(masks, st_xy, xy_size, del_outsides=False, morph_kernel=None):
    '''
    将sam分割图斑的矩阵形式转为要素形式（wkt的矢量列和属性列）
    masks: list[np.darray] sam分割图斑
    st_xy: list[float] 用于坐标转换，左上角x（列方向），y（行方向）坐标
    xy_size: list[float] 用于坐标转换，x\y方向分辨率
    del_outsides: bool 是否删除位于图像边缘的图斑（边缘分割的对象可能不完整）
    morph_kernel: None or cv2.kernel
    '''
    st_time = time.time()
    results = {}
    # features = list(masks[0].keys())
    features = ['predicted_iou', 'stability_score', 'segmentation']
    for f in features:
        results[f] = []

    no_geometry_features = features.copy()
    no_geometry_features.remove('segmentation')
    # no_geometry_features.remove('point_coords')

    st_x, st_y = st_xy[0], st_xy[1]
    x_size, y_size = xy_size[0], xy_size[1]

    # 删除边缘轮廓的情况
    if del_outsides:
        # 遍历masks
        for i in range(len(masks)):
            mask = masks[i]
            segmentation = mask['segmentation']
            # 判断轮廓是否位于边缘
            if np.sum(segmentation) == np.sum(segmentation[1:-1, 1:-1]):
                segmentation = segmentation.astype('uint8')
                if morph_kernel is not None:
                    segmentation = cv2.morphologyEx(segmentation, cv2.MORPH_CLOSE, morph_kernel)
                    segmentation = cv2.morphologyEx(segmentation, cv2.MORPH_OPEN, morph_kernel)
                contours, _ = cv2.findContours(segmentation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                del segmentation

                for contour in contours:
                    if contour.shape[0] > 3:
                        # 记录有效多边形
                        x = np.hstack([contour[:, 0, 0], contour[0, 0, 0]])
                        y = np.hstack([contour[:, 0, 1], contour[0, 0, 1]])
                        x = st_x + x * x_size
                        y = st_y + y * y_size
                        wkt_str = str(list(zip(x, y))).replace('), (', 'pt').replace(', ', ' ').replace('pt', ',')
                        wkt_str = f'POLYGON(({wkt_str[2:-2]}))'
                        results['segmentation'].append(wkt_str)

                        # 记录其他属性列
                        for f in no_geometry_features:
                            results[f].append(mask[f] if f != 'crop_box' else str(mask[f]))
    # 保留边缘轮廓的情况
    else:
        for i in range(len(masks)):
            mask = masks[i]
            segmentation = mask['segmentation'].astype('uint8')
            if morph_kernel is not None:
                segmentation = cv2.morphologyEx(segmentation, cv2.MORPH_CLOSE, morph_kernel)
                segmentation = cv2.morphologyEx(segmentation, cv2.MORPH_OPEN, morph_kernel)
            contours, _ = cv2.findContours(segmentation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            del segmentation

            for contour in contours:
                if contour.shape[0] > 3:
                    # 记录有效多边形
                    x = np.hstack([contour[:, 0, 0], contour[0, 0, 0]])
                    y = np.hstack([contour[:, 0, 1], contour[0, 0, 1]])
                    x = st_x + x * x_size
                    y = st_y + y * y_size
                    wkt_str = str(list(zip(x, y))).replace('), (', 'pt').replace(', ', ' ').replace('pt', ',')
                    wkt_str = f'POLYGON(({wkt_str[2:-2]}))'
                    results['segmentation'].append(wkt_str)

                    # 记录其他属性列
                    for f in no_geometry_features:
                        results[f].append(mask[f] if f != 'crop_box' else str(mask[f]))

    print(f'mask2features used {time.time() - st_time} seconds')
    return results


def wkt2gdf(wkt_list, epsg):
    '''
    wkt形式记录的多边形转为gdf对象
    wkt_list: list[str] wkt形式记录的多边形 str like 'POLYGON ((x1 y1,x2 y2,...))'
    epsg: int 坐标系编号
    '''
    gdf = pd.DataFrame(wkt_list, columns=['geometry'])
    gdf['geometry'] = gdf['geometry'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(gdf, crs=f'EPSG:{epsg}', geometry=gdf['geometry'])

    return gdf


def filter_mask_size(masks, min_size=500, max_size=40000):
    '''
    过滤图斑大小
    masks: SamAutomaticMaskGenerator生成的分割结果
    min_size: int 最小分割图斑大小（单位：像素）
    max_size: int 最大分割图斑大小（单位：像素）
    '''
    areas = np.array([mask['area'] for mask in masks])
    masks = np.array(masks)
    masks = masks[(areas < max_size) & (areas > min_size)]

    return masks


def print_current_memory(process):
    '''
    打印当前进程占用内存情况
    process: psutil.Process
    '''
    memory_info = process.memory_info()
    print(f'当前内存占用：{memory_info.rss / 1024 / 1024} MB')



'''筛选图斑'''
def isContained(geom1, geom2, threshold=0.7):
    '''
    判断gdf2包含gdf1的哪些多边形
    threshold: 如果geom1,geom2相交的面积占geom1面积大于threshold,则认为包含
    '''
    intersections = geom1.intersection(geom2)
    intersect_ids = intersections.index.values
    intersect_ratio = intersections.area.values / geom1.area.values

    return intersect_ids[intersect_ratio > threshold]


def devidePolygons(geoms, resort=True):
    '''
    根据多边形的包含关系，构建多颗二叉树
    geoms: geopandas.GeoDataFrame.geometry
    resort: bool 是否先按面积从大到小排序
    返回值：dict {大图斑索引:[包含的小图斑索引列表],...}
    '''
    if resort:
        # 按面积从大到小排序
        idx = geoms.index.values
        sorted = np.argsort(-geoms.area.values)
        geoms = geoms[idx[sorted]]
    idx = geoms.index.values
    devided = np.zeros(len(idx))
    results = {}
    while 0 in devided:
        i = idx[devided == 0][0]
        polyi = geoms[i]
        contains = isContained(geoms, polyi)
        for c in contains:
            devided[idx == c] = 1
        contains = contains[contains != i]
        results[i] = contains

    return results


def reserveOuter(gdf, idx1, idx2, geotrans, ndwi, thred=0.2):
    '''
    是否保留大轮廓
    '''
    if len(idx2) > 0:
        x_size = geotrans[1]
        y_size = geotrans[5]
        # 大图斑
        outer = gdf.geometry[idx1]
        minx, miny, maxx, maxy = outer.bounds
        cols = int((maxx - minx) / x_size)
        rows = int((miny - maxy) / y_size)
        trans_i = (x_size, 0, minx, 0, y_size, maxy)
        outer = features.rasterize([outer], out_shape=(rows, cols), all_touched=False, transform=trans_i,
                                   default_value=1, fill=0)
        # 其他图斑
        inner = [shapes for shapes in gdf.geometry[idx2]]
        inner = features.rasterize(inner, out_shape=(rows, cols), all_touched=False, transform=trans_i, default_value=2,
                                   fill=0)
        # 其他图斑求并集1（同转栅格）
        diff = np.zeros_like(outer)
        diff[(outer == 1) & (inner == 0)] = 1
        # 若大图斑与并集1的差集所在的区域还有不可忽略的水域，则保留大图斑、小图斑都删除
        st_x = int((minx - geotrans[0]) / x_size)
        st_y = int((maxy - geotrans[3]) / y_size)
        ndwii = ndwi[st_y:st_y + rows, st_x:st_x + cols]
        diff_water = np.sum((ndwii > 0) & (diff == 1))
        w_ratio = diff_water / np.sum(outer)  # 大轮廓减去内部轮廓后的水域面积 / 大轮廓总面积

        return w_ratio > thred, w_ratio

    else:
        return True, 1


def filterOutInn(gdf, ndwi, geotrans):
    '''
    在有包含关系的图斑中选择保留外面大图斑还是内部多个小图斑
    '''
    gdf1 = gdf
    gdf1 = gdf1.sort_values('area', ascending=False).reset_index(drop=True)
    gdf1 = gdf1.to_crs(gdf.crs)
    areas1 = gdf1['area'].values
    geoms1 = gdf1.geometry

    # 统计图斑数量
    n1 = len(gdf1)
    # 水域占比记录
    w_ratio = np.zeros(n1)
    # 记录图斑是否为独立为1组
    isolated = np.zeros(n1)
    # 迭代分组、取舍，直至所有图斑为独立1组
    while 0 in isolated:
        # print(f'******** {np.sum(isolated>0)} filtered *************')
        # 提取待处理图斑
        idx = np.argwhere(isolated == 0).flatten()
        geoms2 = geoms1[idx].copy()

        # 记录该轮各图斑所属组别
        grouped = np.ones(n1) * -1  # 不参该轮处理的标记-1
        grouped[idx] = 0  # 参与处理但未分类的标记0
        k = 1  # 标记组别
        # 从大到小遍历图斑,对多边形分组
        # while 0 in grouped:
        for i in idx:
            # i = idx[grouped[idx]==0][0]
            poly_i = geoms2[i]
            # 查找该图斑是否包含其他图斑（包含指另一图斑落在该图斑范围内面积占另一图斑面积的0.7以上）
            intersections = geoms2[geoms2.intersects(poly_i)].intersection(poly_i)
            intersect_ids = intersections.index.values

            intersect_areas = intersections.area.values
            intersect_ratio = intersect_areas / areas1[intersect_ids]
            selected_ids = intersect_ids[intersect_ratio > 0.7]
            # 判断该图斑及其包含图斑是否已有分组
            regist = np.unique(grouped[selected_ids])
            # 如果已有分组，则所有图斑记录为已有的组别
            if len(regist) == 1 and regist[0] == 0:
                grouped[selected_ids] = k
                k += 1
            # 否则创建新的组别
            else:
                grouped[selected_ids] = regist[-1]

                # 挑选图斑数量为1的组别，记录这些图斑为独立1组，后续不再参与分组、筛选
        for i in np.unique(grouped[grouped != -1]).flatten():
            gi = grouped == i
            if np.sum(gi) == 1:
                isolated[gi] = 1

            # 对图斑数量大于1的组别，在大轮廓和内部多个轮廓间做取舍
            else:
                # 按包含关系建立N棵结构树
                geoms3 = geoms1[gi]
                ntrees = devidePolygons(geoms3, resort=False)
                # 对每棵树判断保留根节点还是子节点
                dels = []
                for p in list(ntrees.keys()):
                    if len(ntrees[p]) == 0:
                        isolated[p] = 1
                        w_ratio[p] = 1
                    else:
                        # 根据（大轮廓-内部轮廓）的水域面积 / 大轮廓总水域面积 大于0.1 决定是否保留大轮廓
                        flag, w_ratioi = reserveOuter(gdf1, p, ntrees[p], geotrans, ndwi)
                        if flag:
                            dels.extend(ntrees[p])
                        else:
                            dels.append(p)
                        w_ratio[p] = w_ratioi
                        w_ratio[ntrees[p]] = w_ratioi

                if len(dels)>0:
                    isolated[np.unique(dels)] = 2

    gdf1['w_ratio'] = w_ratio
    gdf1 = gdf1[isolated == 1]

    return gdf1

def isSamilar(geom2, geom1, threshold=0.7):
    '''
    判断geom1，geom2是否相似
    threshold: 如果geom1,geom2交并比大于threshold,则认为包含
    '''
    intersections = geom2.intersection(geom1)
    intersect_area = intersections.area.values
    iou = intersect_area / (geom2.area + geom1.area - intersect_area)
    intersect_ids = intersections.index.values

    return intersect_ids[iou > threshold]


def filterNms(gdf, scfield='st_score', threshold=0.7):
    '''
    NMS去重
    '''
    if 'area' not in gdf.columns:
        gdf['area'] = gdf.geometry.area
    gdf = gdf.sort_values('area', ascending=False).reset_index(drop=True)
    geoms = gdf.geometry
    scores = gdf[scfield].values
    index = geoms.index.values
    n = len(geoms) # 图斑数量
    devided = np.zeros(n) # 图斑是否已分组标记，0未分组，1已分组
    reserves = np.array([False] * n) # 图斑是否保留标记
    while 0 in devided:
        i = index[devided == 0][0]
        geom1 = geoms[i]
        geoms2 = geoms[geoms.intersects(geom1)] # 提取与geom1相交的图斑
        similar_idx = isSamilar(geoms2, geom1, threshold) # 提取与geom1相似的图斑索引
        devided[similar_idx] = 1 # 标记这些图斑为已分组
        if len(similar_idx) > 1:
            nmax = similar_idx[scores[similar_idx] == scores[similar_idx].max()][0] # 提取相似图斑中得分最高的图斑索引
            reserves[nmax] = True # 保留得分最高的图斑
        else:
            reserves[similar_idx] = True

    return gdf[reserves]


def filterWater(gdf, watermask, geotrans, threshold=0.2):
    '''
    提取水域图斑
    '''
    x_size = geotrans[1]
    y_size = geotrans[5]
    reserves = np.array([False] * len(gdf))
    for i, geom in enumerate(gdf.geometry):
        minx, miny, maxx, maxy = geom.bounds # 提取图斑边界
        cols = int((maxx - minx) / x_size)
        rows = int((miny - maxy) / y_size)
        trans_i = (x_size, 0, minx, 0, y_size, maxy)
        # 转栅格
        geom = features.rasterize([geom], out_shape=(rows, cols), all_touched=False, transform=trans_i, 
                                  default_value=1, fill=0)

        st_x = int((minx - geotrans[0]) / x_size)
        st_y = int((maxy - geotrans[3]) / y_size)
        watermaski = watermask[st_y:st_y + rows, st_x:st_x + cols]

        waters = (watermaski == 1) & (geom == 1)

        if (np.sum(waters) / np.sum(geom==1)) > threshold:
            reserves[i] = True

    return reserves


def filterValidEdge(gdf, watermask, geotrans, border=3, threshold=1):
    '''
    提取有效轮廓——剔除在纯水面过度分割的图斑
    border，threshold: geom边界向外扩border个像素后，如果边界内水域占比达到或超过threshold，则认为是在纯水面
    '''
    x_size = geotrans[1]
    y_size = geotrans[5]
    r, c = watermask.shape[0:2]
    reserves = np.array([False] * len(gdf))
    for i, geom in enumerate(gdf.geometry):
        minx, miny, maxx, maxy = geom.bounds
        minx = max(geotrans[0], minx - (x_size * border))
        miny = max(geotrans[3] + r * y_size, miny + (y_size * border))
        maxx = min(geotrans[0] + c * x_size, maxx + (x_size * border))
        maxy = min(geotrans[3], maxy - (y_size * border))
        cols = int((maxx - minx) / x_size)
        rows = int((miny - maxy) / y_size)
        trans_i = (x_size, 0, minx, 0, -y_size, miny)
        geom = features.rasterize([geom], out_shape=(rows, cols), all_touched=False, transform=trans_i, default_value=1,
                                  fill=0)

        st_x = int((minx - geotrans[0]) / x_size)
        st_y = int((maxy - geotrans[3]) / y_size)
        watermaski = watermask[st_y:st_y + rows, st_x:st_x + cols]

        waters = (watermaski > 0) & (geom == 1)

        if (np.sum(waters) / np.sum(geom)) < threshold:
            reserves[i] = True

    return gdf[reserves]


def filterShape(gdf):
    '''
    形状特征过滤：L/2*sqrt(pi*A*A) <= 1.8 and 最小外接矩形长宽比<=5
    '''
    L = gdf.geometry.length
    A = gdf.geometry.area
    gdf['shp_idx'] = L / (2 * np.sqrt(np.pi * A))
    gdf['mrr_aspt'] = gdf['geometry'].apply(calculate_mbr_elongation_ratio)

    return gdf[(gdf['shp_idx']<=1.8) & (gdf['mrr_aspt']<=5)]


def calculate_mbr_elongation_ratio(poly):
    """
    计算最小外接矩形的长宽比
    参数:
    - poly: 多边形几何对象
    返回:
    - 最小外接矩形的长宽比: 最小外接矩形的长边与短边的比率
    """
    # 计算最小外接矩形
    mbr = poly.minimum_rotated_rectangle

    # 计算最小外接矩形的边长
    x, y = mbr.exterior.coords.xy
    edge_lengths = [((x[i] - x[i - 1]) ** 2 + (y[i] - y[i - 1]) ** 2) ** 0.5 for i in range(1, len(x))]

    # 因为最小外接矩形是矩形，所以它只有两种边长，计算最大和最小边长
    max_length = max(edge_lengths)
    min_length = min(edge_lengths)

    # 计算长宽比
    if min_length == 0:
        return np.nan
    return max_length / min_length


''' 数据准备 '''

def data_uni_run1(rgbpath1,rgbpath2,ndwipath1,ndwipath2,lcpath1,lcpath2,tdtvcpath1,tdtvcpath2):
    '''
    哨兵时序水域
    '''
    os.chdir(rgbpath1)
    rgbfiles = glob.glob('*.tif')
    for rgbfile in rgbfiles:
        print(rgbfile)
        basename = rgbfile[0:-4]
        # 天地图影像重投影
        gdal.Warp(f'{rgbpath2}\\{basename}.tif',rgbfile,format='GTiff',dstSRS='epsg:32650')
        # 天地图影像重投影后范围及栅格大小
        geotif0 = imgpro.geotiffread(f'{rgbpath1}\\{basename}.tif')
        geotrans0 = geotif0.geo_transform
        rows,cols = geotif0.rows,geotif0.cols
        bounds0 = (geotrans0[0],geotrans0[3]+geotrans0[5]*rows,geotrans0[0]+geotrans0[1]*cols,geotrans0[3])

        # 哨兵二水域重投影并裁剪至同一范围
        ndwifile1 = os.path.join(ndwipath1, rgbfile)
        geotif = imgpro.geotiffread(f'{ndwipath1}\\{basename}.tif')
        gdal.Warp(f'{ndwipath2}\\{basename}.tif',ndwifile1,format='GTiff',outputBounds=bounds0,
                srcSRS=geotif.projection,dstSRS=geotif0.projection,width=cols,height=rows)
        # 建筑掩码重投影并裁剪至同一范围
        lcfile1 = os.path.join(lcpath1,rgbfile)
        if os.path.exists(lcfile1):
            geotif = imgpro.geotiffread(lcfile1)
            gdal.Warp(f'{lcpath2}\\{basename}.tif',lcfile1,format='GTiff',outputBounds=bounds0,
                    srcSRS=geotif.projection,dstSRS=geotif0.projection,width=cols,height=rows)
        # 天地图矢量重投影并裁剪至同一范围
        tdtvcfile1 = os.path.join(tdtvcpath1,rgbfile)
        if os.path.exists(tdtvcfile1):
            geotif = imgpro.geotiffread(tdtvcfile1)
            gdal.Warp(f'{tdtvcpath2}\\{basename}.tif',tdtvcfile1,format='GTiff',outputBounds=bounds0,
                    srcSRS=geotif.projection,dstSRS=geotif0.projection,width=cols,height=rows)


def data_uni_run2(ndwifile1,ndwifile2,lcfile1,lcfile2,cntyfile,xysize=2,dst_epsg=3857):
    '''
    哨兵时序水域、建筑投影到3857,并裁剪到cntyfile范围
    '''
    roi = gpd.read_file(cntyfile)
    roi = roi.to_crs(f'epsg:{dst_epsg}')
    bounds = roi.total_bounds.tolist() # minx, miny, maxx, maxy
    cols = int((bounds[2] - bounds[0]) / xysize)
    rows = int((bounds[3] - bounds[1]) / xysize)
    _,_,_,src_epsg = imgpro.getGeoInfo(lcfile1)
    gdal.Warp(lcfile2,lcfile1,format='GTiff',outputBounds=bounds,
                srcSRS=f'epsg:{src_epsg}',dstSRS=f'epsg:{dst_epsg}',width=cols,height=rows)
    _,_,_,src_epsg = imgpro.getGeoInfo(ndwifile1)
    gdal.Warp(ndwifile2,ndwifile1,format='GTiff',outputBounds=bounds,
                srcSRS=f'epsg:{src_epsg}',dstSRS=f'epsg:{dst_epsg}',width=cols,height=rows)


def data_uni_run3(ndwifile1,ndwifile2,lcfile1,lcfile2):
    '''
    哨兵时序水域、建筑投影到3857,并裁剪到哨兵时序水域范围
    '''
    # 哨兵时序水域重投影，重采样到2m
    gdal.Warp(ndwifile2,ndwifile1,format='GTiff',dstSRS='epsg:3857',xRes=2,yRes=2)
    # 哨兵时序水域重投影后范围及栅格大小
    geotif0 = imgpro.geotiffread(ndwifile2)
    geotrans0 = geotif0.geo_transform
    rows,cols = geotif0.rows,geotif0.cols
    bounds0 = (geotrans0[0],geotrans0[3]+geotrans0[5]*rows,geotrans0[0]+geotrans0[1]*cols,geotrans0[3])

    # 建筑重投影并裁剪至同一范围
    geotif = imgpro.geotiffread(lcfile1)
    gdal.Warp(lcfile2,lcfile1,format='GTiff',outputBounds=bounds0,
            srcSRS=geotif.projection,dstSRS=geotif0.projection,width=cols,height=rows)
    

def data_uni_run4(ndwifile1,ndwifile2,lcfile1,lcfile2,tdtfile,xsize=2,ysize=2):
    '''
    哨兵时序水域、建筑投影到3857,并裁剪到天地图范围
    '''
    geotrans0,rows,cols,epsg = imgpro.getGeoInfo(tdtfile)
    bounds0 = (geotrans0[0],geotrans0[3]+geotrans0[5]*rows,geotrans0[0]+geotrans0[1]*cols,geotrans0[3])
    rows = (bounds0[3]-bounds0[1]) / ysize
    cols = (bounds0[2]-bounds0[0]) / xsize
    gdal.Warp(lcfile2,lcfile1,format='GTiff',outputBounds=bounds0,
            dstSRS='epsg:3857',width=cols,height=rows)
    gdal.Warp(ndwifile2,ndwifile1,format='GTiff',outputBounds=bounds0,
            dstSRS='epsg:3857',width=cols,height=rows)


''' 其他输出 '''
def createBounds(geotrans,xsize,ysize,epsg=32650):
    '''
    输出分块范围的矢量
    drange = [xoff,yoff,xsize,ysize]
    '''
    minx = geotrans[0]
    maxx = geotrans[0] + geotrans[1] * xsize
    maxy = geotrans[3]
    miny = geotrans[3] + ysize * geotrans[5]
    net = [Polygon([(minx, maxy), (maxx,maxy), (maxx, miny), (minx, miny),(minx, maxy)])]
    gdf = gpd.GeoDataFrame(geometry=net)
    # 设置研究区域的CRS，例如WGS 84
    crs = f'EPSG:{epsg}'
    gdf.crs = crs

    return gdf

def createBounds2(geotrans,drange,epsg=32650):
    '''
    输出分块范围的矢量
    drange = [xoff,yoff,xsize,ysize]
    '''
    xoff,yoff,xsize,ysize = drange
    minx = geotrans[0] + geotrans[1] * xoff
    maxx = geotrans[0] + geotrans[1] * (xsize + xoff)
    maxy = geotrans[3] + geotrans[5] * yoff
    miny = geotrans[3] + geotrans[5] * (ysize + yoff)
    net = [Polygon([(minx, maxy), (maxx,maxy), (maxx, miny), (minx, miny),(minx, maxy)])]
    gdf = gpd.GeoDataFrame(geometry=net)
    # 设置研究区域的CRS，例如WGS 84
    crs = f'EPSG:{epsg}'
    gdf.crs = crs

    return gdf

def createFishnet(bounds,interval=300,epsg=32650):
    '''
    创建渔网
    bounds： [minx,miny,maxx,maxy]
    interval: 间隔，单位：米
    '''
 
    # 设置研究区域的边界，这里以一个矩形为例
    minx, miny, maxx, maxy = bounds
 
    # 创建一个网格，每个格子的边长等于间隔
    rows = np.arange(miny, maxy + interval, interval)
    cols = np.arange(minx, maxx + interval, interval)
 
    # 创建鱼网的多边形列表
    net = []
    for y in rows:
        for x in cols:
            net.append(Polygon([(x, y), (x + interval, y), (x + interval, y + interval), (x, y + interval)]))
 
    # 将多边形列表转换为GeoDataFrame
    gdf = gpd.GeoDataFrame(geometry=net)
 
    # 设置研究区域的CRS，例如WGS 84
    crs = f'EPSG:{epsg}'
    gdf.crs = crs

    return gdf

def getGeotifDRange(tiffile,bounds):
    '''
    根据已知经纬度范围，获取要读取的图像范围（图像坐标）
    '''
    geotrans,rows,cols,epsg = imgpro.getGeoInfo(tiffile)
    minx, miny, maxx, maxy = bounds
    xoff = int((minx - geotrans[0]) / geotrans[1])
    yoff = int((maxy - geotrans[3]) / geotrans[5])
    xsize = int((maxx - geotrans[0]) / geotrans[1]) - xoff
    ysize = int((miny - geotrans[3]) / geotrans[5]) - yoff

    # return [max(0,xoff),max(0,yoff),min(xsize,cols-max(0,xoff)),min(ysize,rows-max(0,xoff))]
    return [xoff,yoff,xsize,ysize]