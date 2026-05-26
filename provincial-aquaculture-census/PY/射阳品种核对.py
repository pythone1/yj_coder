import pandas as pd
import numpy as np
import os
import re

def extract_species_list(text):
    if pd.isna(text):
        return []
    matches = re.findall(r'([^\d:,，:]+):[\d\.]+', str(text))
    return matches

def process_yz_data(filepath, filename, target_fish, yongtu):
    # 读取数据并设置 index
    filepath_full = os.path.join(filepath, filename)
    df_raw = pd.read_excel(filepath_full)
    df_raw.index = range(len(df_raw))  # 设置固定 index，便于差集精确处理

    # ==================== 筛选有效塘口 ====================
    df = df_raw.copy()
    df = df[pd.to_numeric(df['图斑面积'], errors='coerce').notnull()]
    df['图斑面积'] = pd.to_numeric(df['图斑面积'], errors='coerce')
    df['面积_亩'] = df['图斑面积'] * 0.0015

    if yongtu == '全部':
        df = df[df['用途'].isin(['成品养殖', '苗种培育'])]
    # else:
    #     df = df[df['用途'] == yongtu]

    df = df[df['养殖状态'] == '养殖']

    df['养殖品种名列表'] = df['养殖品种/预计亩产量'].apply(extract_species_list)
    df['养殖品种'] = df['养殖品种名列表'].apply(lambda x: ';'.join(x))

    # ==================== 筛选七鱼塘口 ====================
    mask = df['养殖品种名列表'].apply(lambda lst: any(fish in lst for fish in target_fish))
    df_target = df[mask].copy()
    # df_target = df.copy()
    df_target["所在区县"] = df_target["地址"].astype(str).str.split("-").str[2]
    df_target_index_set = set(df_target.index)

    # ==================== 主体汇总统计 ====================
    result = df_target.groupby(['养殖经营人名称', '身份证号', '统一社会信用代码', '联系方式', '地址']).agg({
        "养殖经营人名称": "first",
        "联系方式": "first",
        "身份证号": "first",
        "统一社会信用代码": "first",
        "地址": "first",
        "面积_亩": "sum",
        "图斑编号": list,
        "养殖品种": lambda x: ';'.join(set(';'.join(x).split(';')))
    })

    # ==================== 地址分层统计 ====================
    address = result['地址'].str.split('-', expand=True)
    address['区镇'] = address[2] + '-' + address[3]
    address_unq = np.unique(address['区镇'].tolist())

    result_tj = pd.DataFrame(index=address_unq, columns=target_fish + ['7鱼合计', '塘口数量'])

    for j in address_unq:
        idx_address = result['地址'].str.contains(j, na=False)
        for i in target_fish:
            idx_fish = result['养殖品种'].str.contains(i)
            result_tj.loc[j, i] = len(result[idx_address & idx_fish])
        idx_any_fish = result['养殖品种'].apply(lambda x: any(f in x for f in target_fish))
        result_tj.loc[j, '7鱼合计'] = len(result[idx_address & idx_any_fish])
        result_tj.loc[j, '塘口数量'] = len(df_target[df_target['地址'].str.contains(j, na=False)])

    # ==================== df_target 导出列 ====================
    df_target_export = df_target[['养殖经营人名称', '身份证号', '统一社会信用代码', '地址', '所在区县', '联系人', '联系方式',
                                  '养殖品种/预计亩产量', '养殖品种', '图斑编号', '面积_亩',
                                  '池塘所有权', '池塘所有权人名称', '池塘所有权人证件号码', '用途']]

    # ==================== df_qt 差集部分 ====================
    df_all_yz = df_raw.copy()
    df_all_yz.index = range(len(df_all_yz))
    df_all_yz = df_all_yz[pd.to_numeric(df_all_yz['图斑面积'], errors='coerce').notnull()]
    df_all_yz['图斑面积'] = pd.to_numeric(df_all_yz['图斑面积'], errors='coerce')
    df_all_yz['面积_亩'] = df_all_yz['图斑面积'] * 0.0015
    df_all_yz = df_all_yz[df_all_yz['养殖状态'] == '养殖']

    # 使用 index 差集：只保留非七鱼塘口
    df_qt = df_all_yz[~df_all_yz.index.isin(df_target_index_set)].copy()
    df_qt["所在区县"] = df_qt["地址"].astype(str).str.split("-").str[3]
    df_qt['养殖品种名列表'] = df_qt['养殖品种/预计亩产量'].apply(extract_species_list)
    df_qt['养殖品种'] = df_qt['养殖品种名列表'].apply(lambda x: ';'.join(x))
    df_qt = df_qt[['养殖经营人名称', '身份证号', '统一社会信用代码', '地址', '所在区县', '联系人', '联系方式',
                   '养殖品种/预计亩产量', '养殖品种', '图斑编号', '面积_亩',
                   '池塘所有权', '池塘所有权人名称', '池塘所有权人证件号码', '用途']]
    #
    output_path = os.path.join(filepath, f'{filename.replace(".xlsx", f"虾蟹明细表.xlsx")}')
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df_target.to_excel(writer, sheet_name="七鱼明细", index=False)
        df_qt.to_excel(writer, sheet_name="其他鱼明细", index=False)
    
    
    # ==================== 导出 ====================
    address_parts = df_raw['地址'].astype(str).str.split('-', expand=True)
    quxian_list = sorted(address_parts[2].dropna().unique())
    # for qx in quxian_list:
    #     # 筛选当前区县的七鱼和非七鱼塘口
    #     df_target_qx = df_target_export[df_target_export['地址'].str.contains(qx, na=False)].copy()
    #     df_qt_qx = df_qt[df_qt['地址'].str.contains(qx, na=False)].copy()
    #     if df_target_qx.empty and df_qt_qx.empty:
    #         continue  # 如果两张表都为空就跳过
    #     # 构建文件路径
    #     output_path = os.path.join(filepath, f'{filename.replace(".xlsx", f"_{qx}七鱼明细表.xlsx")}')
    #     with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    #         df_target_qx.to_excel(writer, sheet_name="成品养殖+苗种培育七鱼明细", index=False)
    #         df_qt_qx.to_excel(writer, sheet_name="其他鱼明细", index=False)
    result_tj.to_excel(os.path.join(filepath, filename.replace('.xlsx', '主体数量统计.xlsx')))
    result.to_excel(os.path.join(filepath, filename.replace('.xlsx', '主体清单.xlsx')))

if __name__ == "__main__":
    rawpath = r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250903\20251201'
    filename = '十一点射阳最新数据.xlsx'
    # fish_list = ['鳊鲂', '鲫鱼', '鲈鱼', '泥鳅']
    fish_list = ['鳊鲂', '鲫鱼', '鲈鱼', '泥鳅', '乌鳢', '黄鳝', '蛙']
    # fish_list = ['青虾', '河蟹']
    # fish_list = ['青虾', '河蟹']

    process_yz_data(rawpath, filename, fish_list, yongtu="全部")
