import pandas as pd
import re
from pypinyin import lazy_pinyin, Style

# 读取文件
df = pd.read_excel(r"E:\水产种质资源保护区\20251124\江苏省水产种质资源保护区.xls")

# 字段名
col = "地区+品种"

# 清洗：删除符号，再只保留中文汉字
def clean_text(s):
    if pd.isna(s):
        return ""
    s = str(s)
    # 去标点符号
    s = re.sub(r"[、，,（）()《》<>·\s\-—/]", "", s)
    # 只保留中文
    s = re.sub(r"[^一-龥]", "", s)
    return s

# 拼音首字母（大写）
def get_initials(s):
    if not s:
        return ""
    initials = lazy_pinyin(s, style=Style.FIRST_LETTER)
    return "".join(i.upper() for i in initials)

# 清洗
df["地区品种_clean"] = df[col].apply(clean_text)

# 生成编码
df["编码"] = df["地区品种_clean"].apply(get_initials)

# 长度
df["编码长度"] = df["编码"].str.len()

# 重复判断
df["是否重复"] = df["编码"].duplicated(keep=False)

# 输出
print(df)

# 保存
df.to_excel(r"E:\水产种质资源保护区\20251124\编码结果.xlsx", index=False)
