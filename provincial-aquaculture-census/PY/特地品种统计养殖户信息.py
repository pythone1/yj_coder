import pandas as pd
import os
os.chdir(r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250429')
# 读取Excel文件
df = pd.read_excel(r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250429\常州市.xlsx')  # 替换为你的文件名

# 要筛选的品种列表
species_list = ['鲫鱼', '鳊鲂', '鲈鱼', '乌鳢', '黄鳝', '牛蛙', '泥鳅']

# 创建一个 ExcelWriter 对象用于保存结果
with pd.ExcelWriter('养殖品种筛选结果.xlsx', engine='openpyxl') as writer:
    for species in species_list:
        # 筛选包含该品种的数据
        df_species = df[df['养殖品种/预计亩产量'].astype(str).str.contains(species, na=False)]

        # 对“养殖经营人名称”和“主体id”去重
        df_species_unique = df_species.drop_duplicates(subset=['养殖经营人名称', '主体id'])

        # 写入总表（例如“鲫鱼-总表”）
        df_species_unique.to_excel(writer, sheet_name=f'{species}-总表', index=False)

        # # 基于地址按区县拆分
        # for district, group in df_species_unique.groupby(df_species_unique['地址'].astype(str).str.split('-').str[2]):
        #     sheet_name = district.strip()[:31]  # Excel表名不能超过31字符
        #     # 为了避免不同品种重名区县冲突，加品种前缀
        #     full_sheet_name = f"{species[:3]}_{sheet_name}"
        #     group.to_excel(writer, sheet_name=full_sheet_name, index=False)
