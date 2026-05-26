import geopandas as gpd
import pandas as pd
import numpy as np
import json
import datetime
import os

# ---------------------------
# 你的前半段代码（加载 Excel、gpkg、合并等）
# 假设变量名与原脚本一致：
# excel_df, gdf_original, gdf_template, gdf_result, gdf_template_empty
# 我这里直接放回你原始流程（如需整体替换可以把下面部分替换为你的读取逻辑）
# ---------------------------
#
# （——把你原来读取和合并的代码放在这里 ——）
# 为演示，我直接把你给的代码片段放回（不改动原逻辑）
excel_file = r'D:\Users\xwechat_files\wxid_4668346683612_4126\msg\file\2025-10\123.xlsx'
excel_df = pd.read_excel(excel_file)
print(len(excel_df))

gpkg_file = r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250902\宜兴市池塘图斑库.gpkg'
gdf_original = gpd.read_file(gpkg_file)

template_gpkg_file = r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250902\1.gpkg'
gdf_template = gpd.read_file(template_gpkg_file)

excel_df['图斑编号'] = excel_df['图斑编号'].astype(str)
gdf_original['tbid'] = gdf_original['tbid'].astype(str)

gdf_filtered = gdf_original[gdf_original['tbid'].isin(excel_df['图斑编号'])]
print(gdf_filtered)
gdf_filtered = gdf_filtered[['tbid', 'geometry']]

gdf_result = pd.merge(gdf_filtered, excel_df, left_on='tbid', right_on='图斑编号', how='left')
gdf_result = gdf_result.drop(columns=['tbid'])
gdf_result = gpd.GeoDataFrame(gdf_result, geometry='geometry')

gdf_template_empty = gdf_template.iloc[0:0]

if gdf_template.crs != gdf_result.crs:
    gdf_result = gdf_result.to_crs(gdf_template.crs)

gdf_template_empty = pd.concat([gdf_template_empty, gdf_result], ignore_index=True)
# ---------------------------
# 到这里为止，数据合并完成，开始做“稳健转换并清空Na”步骤
# ---------------------------

def is_datetime_object(x):
    return isinstance(x, (pd.Timestamp, datetime.datetime, np.datetime64))

def looks_like_excel_serial_number(val):
    """粗略判断一个数值是否可能是 Excel 的日期序号（Windows 1900 系统）
       我取范围 20000–60000 覆盖较多现代日期；比例判定在列级别使用。"""
    try:
        fv = float(val)
    except Exception:
        return False
    return 20000 <= fv <= 60000

def excel_serial_to_datetime(val):
    """把 Excel 的序列号（1900 系统）转为 pandas.Timestamp"""
    try:
        origin = pd.Timestamp('1899-12-30')  # 通用做法，能兼容大多数 excel -> pd 转换
        ts = origin + pd.to_timedelta(float(val), unit='D')
        return ts
    except Exception:
        return None

def convert_date_like_cell(x):
    """把单个单元格转换为期望的字符串（日期优先转为可读字符串），空值统一返回 ''"""
    # 统一把 pandas/np 的缺失视为空
    if pd.isna(x):
        return ""
    # 原始字符串，尽量保持原貌（比如 '2026年6月'）
    if isinstance(x, str):
        s = x.strip()
        if s.lower() in ("nan", "nat", "none", ""):
            return ""
        return s
    # pandas / python datetime 类型
    if is_datetime_object(x):
        try:
            ts = pd.to_datetime(x, errors='coerce')
            if pd.isna(ts):
                return ""  # 如果无法解析则返回空
            # 若无时间成分则只保留日期
            if ts.hour == 0 and ts.minute == 0 and ts.second == 0:
                return ts.strftime("%Y-%m-%d")
            else:
                return ts.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return str(x)
    # 数字类型：可能是 Excel 序列（日期），也可能就是数值——由列级判断决定是否当日期处理
    if isinstance(x, (int, float, np.integer, np.floating)):
        # 如果明显是整数/浮点但又在 Excel 日期区间，尝试转换为日期字符串（再做可靠性判断）
        if looks_like_excel_serial_number(x):
            ts = excel_serial_to_datetime(x)
            if ts is not None and 1900 <= ts.year <= 2100:
                if ts.hour == 0 and ts.minute == 0 and ts.second == 0:
                    return ts.strftime("%Y-%m-%d")
                else:
                    return ts.strftime("%Y-%m-%d %H:%M:%S")
        # 否则直接转为字符串，但去掉科学计数法和多余小数
        # 保持整数风格如果是整数
        if float(x).is_integer():
            return str(int(x))
        else:
            return str(x)
    # 容器类型（list/tuple/dict）——用 json 串行化（保中文）
    if isinstance(x, (list, tuple, dict)):
        try:
            return json.dumps(x, ensure_ascii=False)
        except Exception:
            return str(x)
    # 其它类型（比如 Decimal、bool 等）——安全转字符串
    s = str(x)
    if s in ("nan", "NaT", "None", "NoneType"):
        return ""
    return s

def convert_general_cell(x):
    """非日期列的逐单元格字符串化（保留原字符串），空值 -> ''"""
    if pd.isna(x):
        return ""
    if isinstance(x, str):
        s = x.strip()
        if s.lower() in ("nan", "nat", "none"):
            return ""
        return s
    if isinstance(x, (list, tuple, dict)):
        try:
            return json.dumps(x, ensure_ascii=False)
        except Exception:
            return str(x)
    # 其余直接 str，尽量避免 pandas.display 把大数转科学计数法
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    if isinstance(x, (float, np.floating)):
        # 保留浮点原样
        return str(x)
    # boolean / other
    s = str(x)
    if s in ("nan", "NaT", "None", "NoneType"):
        return ""
    return s

# 现在对每一列做判断并转换（跳过 geometry 列）
geom_col = gdf_template_empty.geometry.name if hasattr(gdf_template_empty, "geometry") else "geometry"
print("geometry 列名：", geom_col)

# 我会记录被判定为日期列的列名，便于 debug
date_like_cols = []

for col in list(gdf_template_empty.columns):
    if col == geom_col:
        continue

    ser = gdf_template_empty[col]

    # 统计信息，用于判断
    nonnull = ser.dropna()
    n_nonnull = len(nonnull)
    if n_nonnull == 0:
        # 全空列，直接填成空字符串列（object dtype）
        gdf_template_empty[col] = ""
        continue

    # 判断列是否包含 datetime 对象或 pandas datetime dtype
    has_dt_objects = nonnull.apply(lambda x: is_datetime_object(x)).any()
    dtype_is_dt = pd.api.types.is_datetime64_any_dtype(ser)

    # 判断列中有多少值为可能的 Excel 日期序号（20000-60000）
    num_excel_like = nonnull.apply(lambda x: isinstance(x, (int, float, np.integer, np.floating)) and looks_like_excel_serial_number(x)).sum()
    ratio_excel_like = num_excel_like / n_nonnull

    # 若列包含 datetime 对象 或 dtype 是 datetime 或 有较大比例的 excel-like 数值，则把整列当作“日期列”处理
    if has_dt_objects or dtype_is_dt or ratio_excel_like >= 0.4:
        date_like_cols.append(col)
        # 应用日期优先的转换函数
        gdf_template_empty[col] = ser.apply(convert_date_like_cell)
    else:
        # 普通列，逐单元格字符串化
        gdf_template_empty[col] = ser.apply(convert_general_cell)

# 最后，再一次统一把常见的“nan/NaT/None”等字符串替换为空字符串以保险
for col in gdf_template_empty.columns:
    if col == geom_col:
        continue
    # 只对 object 列操作
    if gdf_template_empty[col].dtype == object:
        gdf_template_empty[col] = gdf_template_empty[col].replace(
            to_replace=["nan", "NaT", "None", "NoneType", "NaN"],
            value="",
            regex=False
        )

print("被判定为日期列：", date_like_cols)
# 检查是否还剩下 NaN/NaT
remaining_na = {col: int(gdf_template_empty[col].isna().sum()) for col in gdf_template_empty.columns if col != geom_col}
print("转换后各列剩余缺失计数（应全部为0）：", remaining_na)

# 保存到 gpkg
output_gpkg_file = r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250902\output.gpkg'
# 确保输出目录存在
os.makedirs(os.path.dirname(output_gpkg_file), exist_ok=True)

try:
    gdf_template_empty.to_file(output_gpkg_file, layer='updated_layer', driver="GPKG")
    print(f"文件已成功保存到: {output_gpkg_file}")
except Exception as e:
    print("写出失败，异常信息：", e)
    # 若出问题，可把 schema 打印出来 debug
    try:
        print("输出时推断 schema:", gdf_template_empty.dtypes)
    except Exception:
        pass



# import geopandas as gpd
# import pandas as pd
#
# # 读取 Excel 文件，将“图斑编号”列作为索引
# excel_file = r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250902\宜兴市鳊鲫鱼养殖及监管信息表.xlsx'
# excel_df = pd.read_excel(excel_file)
#
# # 读取原始 gpkg 文件
# gpkg_file = r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250902\宜兴市池塘图斑库.gpkg'
# gdf_original = gpd.read_file(gpkg_file)
#
# # 确保“图斑编号”和“tbid”是字符串类型，防止匹配错误
# excel_df['图斑编号'] = excel_df['图斑编号'].astype(str)
# gdf_original['tbid'] = gdf_original['tbid'].astype(str)
#
# # 找出不在原始池塘图斑库中的图斑编号
# not_in_gdf = excel_df[~excel_df['图斑编号'].isin(gdf_original['tbid'])]
#
# # 打印结果，查看不在原始池塘图斑库中的图斑编号
# print(f"不在池塘图斑库中的图斑编号：")
# print(not_in_gdf)
#
# # 如果需要保存这些数据到文件，可以用以下代码
# not_in_gdf.to_excel(r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250902\not_in_gdf.xlsx', index=False)
#
