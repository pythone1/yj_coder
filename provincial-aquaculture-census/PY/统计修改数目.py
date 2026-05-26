import pandas as pd

# 读取Excel文件并提取图斑编号列（假设图斑编号列名为“图斑编号”）
def extract_ids_from_excel(file_path):
    df = pd.read_excel(file_path)
    return set(df['池塘id'].dropna().values)

# 读取A/B两个Excel文件，提取图斑编号集合set1
set1 = extract_ids_from_excel(r'E:\全省养殖池溏上图入库普查\疑点核查\20250418修改信息统计\苏州市\20250327苏州市疑点信息表(去除未使用及软件疑点).xlsx').union(extract_ids_from_excel(r'E:\全省养殖池溏上图入库普查\疑点核查\20250418修改信息统计\苏州市\20250402苏州市疑点信息.xlsx'))

# 读取C/D两个Excel文件，提取图斑编号集合set2
set2 = extract_ids_from_excel(r'E:\全省养殖池溏上图入库普查\疑点核查\20250418修改信息统计\苏州市\20250417苏州市疑点信息表.xlsx')

removed_set = set1 - set2
all_set = set1.union(set2)
removed_count = len(removed_set)
all_count = len(all_set)

# 输出结果
print(all_count,removed_count)
