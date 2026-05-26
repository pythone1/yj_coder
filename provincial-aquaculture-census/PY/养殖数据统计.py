import pandas as pd

# 读取数据
df = pd.read_excel(r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250626\镇江市.xlsx')
species_keywords = ['鲫鱼', '鳊鲂']
# district_keywords = ['高淳区', '溧水区', '江宁区', '雨花台区', '栖霞区', '浦口区', '江北新区', '六合区']

district_keywords = ['京口区', '润州区', '丹徒区', '扬中市', '丹阳市', '句容市','镇江经济技术开发区','镇江高新技术产业开发区']

# 创建一个空的数据框来存储最终的统计结果
# 第一行是品种名称，每个品种下面是 "养殖主体数/个", "池塘个数/个", "池塘面积/亩"
columns = []
for specie in species_keywords:
    columns += [f'{specie}_养殖主体数/个', f'{specie}_池塘个数/个', f'{specie}_池塘面积/亩']

# 创建空的最终结果DataFrame
result = pd.DataFrame(columns=['区县'] + columns)

# 进行统计并将结果添加到最终表格中
for district in district_keywords:
    # 初始化当前区县的统计结果
    current_result = {'区县': district}

    # 遍历每个品种，统计相关数据
    for specie in species_keywords:
        # 筛选出当前区县和品种的数据
        subset = df[
            (df['地址'].str.contains(district, na=False)) & (df['养殖品种/预计亩产量'].str.contains(specie, na=False))]

        if subset.empty:
            # 如果没有数据，则为该品种赋值0
            current_result[f'{specie}_养殖主体数/个'] = 0
            current_result[f'{specie}_池塘个数/个'] = 0
            current_result[f'{specie}_池塘面积/亩'] = 0
        else:
            # 强制转换“图斑面积”为数值类型，并将无法转换的值变为NaN
            subset['图斑面积'] = pd.to_numeric(subset['图斑面积'], errors='coerce')

            # 统计养殖主体个数（去重“养殖经营人名称”）
            subject_count = subset.drop_duplicates(subset=['养殖经营人名称', '身份证号', '统一社会信用代码']).shape[0]

            # 统计池塘个数（去重“图斑编号”）
            pond_count = subset['图斑编号'].nunique()

            # 计算池塘面积（总面积 * 0.0015 转换为亩），忽略NaN
            total_area = subset.drop_duplicates(subset='图斑编号')['图斑面积'].sum() * 0.0015

            # 将结果添加到当前区县的统计结果中
            current_result[f'{specie}_养殖主体数/个'] = subject_count
            current_result[f'{specie}_池塘个数/个'] = pond_count
            current_result[f'{specie}_池塘面积/亩'] = total_area

    # 将当前区县的统计结果添加到结果数据框中
    result = pd.concat([result, pd.DataFrame([current_result])], ignore_index=True)

# 保存结果为新的 Excel 文件
output_path = r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250626\20250626镇江市鳊鲂鲫鱼养殖主体统计.xlsx'
result.to_excel(output_path, index=False)

