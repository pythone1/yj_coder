import re
import pandas as pd
df = pd.read_excel(r'E:\全省养殖池溏上图入库普查\合规性检查\20250520\所有权人证件号码非18位.xlsx')
BZ = '池塘所有权人身份证号不是18位'
df[BZ]=''
# 先清洗“池塘所有权人证件号码”列：去除所有空格和英文单引号
df['池塘所有权人证件号码'] = df['池塘所有权人证件号码'].astype(str).str.replace(r"[ '\u3000]", '', regex=True)

# 身份证号校验函数（是否为18位字母数字）
is_id = lambda x: isinstance(x, str) and re.fullmatch(r'[A-Za-z0-9]{18}', x) is not None

# 筛选：池塘所有权是“个人”，证件号码非空但格式不正确
idx = df[
    (df['池塘所有权'] == '个人') &
    (df['池塘所有权人证件号码'].str.strip() != '') &
    ~df['池塘所有权人证件号码'].apply(is_id)
].index

# 添加备注
df.loc[idx, BZ] += "池塘所有权人身份证号不是18位，"

df.to_excel(r'E:\全省养殖池溏上图入库普查\合规性检查\20250520\池塘所有权人身份证号不是18位(删除空格引号).xlsx')
