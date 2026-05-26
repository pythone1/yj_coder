import os,glob
import pandas as pd
import numpy as np

BZ = '必填项检查'

def requiredFieldCheck(df,name):
    '''
    必填项检查
    '''
    fclss = {
        '填报人': ['用户类别','手机号码'],
        '养殖经营人': ['养殖主体类型','养殖经营人名称','证件号'],
        '池塘所在地址': ['市*','县（市、区）*','乡镇（街道）*','村（社区）*'],
        '联系人': ['联系人*','联系方式*'],
        '养殖状态': ['养殖状态*'],
        '所有权人': ['池塘所有权*','池塘所有权人名称*'],
        '池塘信息': ['面积','用途*','水体类型*','养殖方式*','养殖类型*','养殖水体*','养殖品种/预计亩产量*','尾水集中排放期*','清塘淤泥处理方式*','有无尾水处理*'],
        '清塘淤泥处置': ['处置频率*'],
        '尾水处理':['尾水处理工艺*'],
        '尾水净化区面积':['尾水净化区面积*']
    }
    df['证件号'] = df['身份证号'] + df['统一社会信用代码']
    df['面积'] = df['合同面积'] + df['净水面面积']


    # 证件号码必填
    idx = df[df['证件号'] == ''].index
    df.loc[idx,BZ] += f"身份证号码、统一社会信用代码均未填，"

    # 养殖主体类型* 为个人时，身份证号*必填
    idx = df[(df['养殖主体类型']=='个人') & (df['身份证号']=='')].index
    df.loc[idx,BZ] += f"个人养殖未填写身份证号，"

    # 养殖主体类型* 为集体/公司时，统一社会信用代码必填
    idx = df[(df['养殖主体类型']=='集体/公司') & (df['统一社会信用代码']=='')].index
    df.loc[idx,BZ] += f"集体/公司养殖未填写统一社会信用代码，"
    
    if name=='养殖':
        # 养殖状态为“养殖”且用途不是休闲垂钓时的必填
        df1 = df[(df['养殖状态']=='养殖') & (df['用途']!='休闲垂钓') & (df['用途']!='尾水净化')]
        for k in ['面积','水体类型','养殖方式','养殖品种/预计亩产量','尾水集中排放期','清塘淤泥处理方式','有无尾水处理']:
            idx = df1[df1[k] == ''].index
            df.loc[idx,BZ] += f"{k}未填，"
        
        # 养殖状态为“养殖”且用途是休闲垂钓或尾水净化时的必填
        df1 = df[(df['养殖状态']=='养殖') & (df['用途']=='休闲垂钓')]
        for k in ['面积','尾水集中排放期','清塘淤泥处理方式','有无尾水处理']:
            idx = df1[df1[k] == ''].index
            df.loc[idx,BZ] += f"{k}未填，"

        df1 = df[(df['养殖状态']=='养殖') & (df['用途']=='尾水净化')]
        for k in ['面积','尾水集中排放期','清塘淤泥处理方式','有无尾水处理']:
            idx = df1[df1[k] == ''].index
            df.loc[idx,BZ] += f"{k}未填，"
        
        
        # 清塘淤泥处理方式*不等于“不处置”时的必填
        df1 = df[df['清塘淤泥处理方式']!="不处置"]
        idx = df1[df1['处置频率'] == ''].index
        df.loc[idx,BZ] += f"处置频率未填，"

        # 有无尾水处理*填写“有”时的必填
        df1 = df[df['有无尾水处理']=="有"]
        idx = df1[df1['尾水处理工艺'] == ''].index
        df.loc[idx,BZ] += f"尾水处理工艺未填，"
        
        # 有尾水处理、且非原位修复时的必填
        df1 = df[df['尾水处理工艺']!='']
        df2 = df1[df1['尾水处理工艺']!='原位修复']
        idx = df2[df2['尾水净化区面积'] == ''].index
        df.loc[idx,BZ] += f"尾水净化区面积未填，"

        # 面积大于50亩必填“是否完成池塘标准化改造*”
        # df['图斑面积（亩）']=(df['图斑面积_y'].astype(float))*0.0015
        df['图斑面积_y'] = pd.to_numeric(df['图斑面积_y'], errors='coerce')
        idx = df[(df['图斑面积_y']>=50) & (df['是否完成池塘标准化改造']=='')].index
        df.loc[idx,BZ] += f"50亩以上池塘未填 是否完成池塘标准化改造*\n"

    return df



if __name__ == "__main__":
    pth = r'E:\全省养殖池溏上图入库普查\疑点核查\0714南京'
    os.chdir(pth)
    xls_file = '0714浦口区疑点信息表.xlsx'

    if os.path.isdir(xls_file):
        files = glob.glob(f"{xls_file}\\*.xlsx")
        df_list = []
        for f in files:
            print(f"read {f}")
            df_list.append(pd.read_excel(f, dtype=str))  #, skiprows=1
        ctxx = pd.concat(df_list,ignore_index=True)
    else:
        ctxx = pd.read_excel(xls_file, dtype=str)

    # 未填项设置为''
    for c in ctxx.columns:
        ctxx.loc[ctxx[c]=='/',c] = ''
    ctxx= ctxx.fillna('')
    ctxx[BZ]=''

    # 未使用必填项检查
    df_wsy = ctxx[ctxx['填报状态'].str.contains('已填报非养殖')]
    df_wsy = requiredFieldCheck(df_wsy,name='未使用')
    df_wsy.to_excel("必填项检查_未使用.xlsx",index=False)

    # 养殖必填项检查
    df_yz = ctxx[ctxx['填报状态'].str.contains('已填报养殖')]
    df_yz = requiredFieldCheck(df_yz,name='养殖')
    df_yz.to_excel("必填项检查_养殖.xlsx",index=False)
    
    # df3 = df2.dropna(subset=[BZ])
    # outfile = f"必填项检查.xlsx"

    
    