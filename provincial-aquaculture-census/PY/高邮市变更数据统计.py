import pandas as pd
import os

# ===== 设置工作目录 =====
os.chdir(r'E:\全省养殖池溏上图入库普查\PY\四条鱼专项\高邮市变动统计')

# ===== 参数设置 =====
path_710 = r"高邮市0710主体清单明细表（精确到塘口）.xlsx"
path_804 = r"0804高邮市晚主体清单明细表（精确到塘口）.xlsx"
output_path = r"高邮市7月10日至8月4日变动数据.xlsx"
id_col = "图斑编号"

# ===== 读取数据（保留原始列顺序）=====
df_710 = pd.read_excel(path_710, dtype=str).fillna("")
df_804 = pd.read_excel(path_804, dtype=str).fillna("")

# 记录列顺序模板（以804为主）
column_order = df_804.columns.tolist()

# 创建图斑编号 -> 行的映射字典（不设为索引）
dict_710 = {row[id_col]: row for _, row in df_710.iterrows()}
dict_804 = {row[id_col]: row for _, row in df_804.iterrows()}

# 所有图斑编号集合
all_ids = set(dict_710.keys()).union(set(dict_804.keys()))

# ===== 分类处理 =====
unchanged, modified, added, deleted = [], [], [], []

for gid in all_ids:
    in_710 = gid in dict_710
    in_804 = gid in dict_804

    if in_710 and in_804:
        row_710 = dict_710[gid]
        row_804 = dict_804[gid]

        # 对比除图斑编号外的所有字段
        comparable_cols = [col for col in column_order if col != id_col]
        is_same = all(row_710[col] == row_804[col] for col in comparable_cols)

        new_row = row_804.copy()
        new_row["变更理由"] = "不变" if is_same else "修改"
        (unchanged if is_same else modified).append(new_row)

    elif in_804:
        new_row = dict_804[gid].copy()
        new_row["变更理由"] = "新增"
        added.append(new_row)

    elif in_710:
        new_row = dict_710[gid].copy()
        new_row["变更理由"] = "删除"
        deleted.append(new_row)

# ===== 合并结果 =====
result_df = pd.DataFrame(unchanged + modified + added + deleted)

# 确保列顺序（以8月4日为主）+ 变更理由
final_columns = column_order + ["变更理由"]
result_df = result_df[[col for col in final_columns if col in result_df.columns]]

# 保存结果
result_df.to_excel(output_path, index=False)
print(f"✅ 处理完成，共 {len(result_df)} 条数据，已保存至：{output_path}")
