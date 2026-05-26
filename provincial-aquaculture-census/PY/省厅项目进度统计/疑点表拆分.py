import os,glob
from datetime import datetime

from CTXXTBYD import *

xlsfile = r'E:\江苏省养殖池塘上图入库项目\质控检查\宿迁0313\宿迁市疑点清单0313.xlsx'
outpath = r'E:\江苏省养殖池塘上图入库项目\质控检查\宿迁0313\宿迁市疑点清单'
df=pd.read_excel(xlsfile)
field='地址'
yd_columns = ['名称疑点','位置疑点','水面面积疑点','合同面积疑点','池塘合并疑点','亩产量疑点']
xzq = np.unique(df[field].values)
xzq = ['-'.join(x.split('-')[0:-1]) for x in xzq]
xzq = list(set(xzq))
address = df[field].str.split('-',expand=True)
address = address[0] + '-' + address[1] + '-' + address[2] + '-' + address[3]
i=0
for x in xzq:
    subsets = df[address==x]
    # for c in yd_columns:
    #     v = np.unique(subsets[c].values)
    #     if (len(v) == 1) & (v[0] == '无异常'):
    #         subsets = subsets.drop(columns=[c])
    subsets.to_excel(os.path.join(outpath,f'{x}.xlsx'))
    i=i+len(subsets)
    print(i)
