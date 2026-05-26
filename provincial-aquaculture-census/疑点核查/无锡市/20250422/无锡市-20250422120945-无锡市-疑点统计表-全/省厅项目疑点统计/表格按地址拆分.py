import os,glob
from datetime import datetime

from CTXXTBYD import *

xlsfile = r'E:\江苏省养殖池塘上图入库项目\质控检查\0415全省（所有权人非公司）\苏北\宿迁市.xlsx'
outpath = r'E:\江苏省养殖池塘上图入库项目\质控检查\0415全省（所有权人非公司）\苏北'
df=pd.read_excel(xlsfile)
field='地址'
xzq = np.unique(df[field].values)
xzq = ['-'.join(x.split('-')[0:-2]) for x in xzq]
xzq = list(set(xzq))
address = df[field].str.split('-',expand=True)
address = address[0] + '-' + address[1] + '-' + address[2]
i=0
for x in xzq:
    subsets = df[address==x]
    subsets.to_excel(os.path.join(outpath,f'{x}.xlsx'))
    i=i+len(subsets)
    print(i)