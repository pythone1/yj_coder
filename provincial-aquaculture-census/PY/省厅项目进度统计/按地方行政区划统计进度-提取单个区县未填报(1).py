import os

import pandas as pd

pth = r'E:\江苏省养殖池塘上图入库项目\进度统计\全省进度\20250418\未填报图斑拆分'
os.chdir(pth)

xlsfile = '池塘信息表--填报图斑统计（按校对状态）-未填报图斑对应地方行政区划.xlsx'
name = '丹阳市'
df = pd.read_excel(xlsfile,index_col=[0,1])
df['区县'] = df.index.get_level_values(1)
idx1 = df['区县'].str.contains(name)
idx2 = df['地方区划'].str.contains(name)
idx = idx1 | idx2
df.loc[idx,:].drop(columns=['区县']).to_excel(xlsfile.replace('.xlsx',f'-{name}.xlsx'))




# namelist=['南京市:NJS','镇江市:ZJS','扬州市:YZS','常州市:CZS','无锡市:WXS','苏州市:SZS','南通市:NTS',
#           '泰州市:TZS','淮安市:HAS','宿迁市:SQS','徐州市:XZS','盐城市:YCS','连云港市:LYGS']
# for name in namelist:
#     name1 = name.split(':')[0]
#     name2 = name.split(':')[1]
#     df = pd.read_excel(xlsfile,index_col=[0,1])
#     df['市'] = df.index.get_level_values(1)
#     idx1 = df['TBID'].str.contains(name2)
#     idx2 = df['地方区划'].str.contains(name1)
#     idx = idx1 | idx2
#     df.loc[idx,:].drop(columns=['市']).to_excel(xlsfile.replace('.xlsx',f'-{name1}.xlsx'))
