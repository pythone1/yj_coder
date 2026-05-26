import os,glob

import geopandas as gpd
import pandas as pd
import numpy as np
from datetime import datetime as dt

if __name__ == '__main__':
    datapath = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\图斑汇总\20241225江苏省池塘图斑'
    os.chdir(datapath)

    orifile0 = '20241225江苏省池塘图斑.shp'
    orifile1 = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\图斑汇总\外发池塘\大丰区池塘图斑_ori.shp'
    newfile = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\图斑汇总\外发池塘\大丰区池塘图斑_20241227更新_check.shp'
    outfile = '20250104江苏省池塘图斑.shp'

    # read
    st_time = dt.now()
    # gdf0 = gpd.read_file(orifile0)
    # gdf01 = gpd.read_file(orifile1)
    gdf1 = gpd.read_file(newfile)
    # ed_time = dt.now()
    # spd_time = ed_time - st_time
    # print(f'读数据，长度{len(gdf0)}，用时{spd_time} s')
    # print(f'01长度{len(gdf01)}')

    # # 删除图斑
    # st_time = dt.now()
    # tbid1 = gdf1['TBID'].values
    # cnt = 0
    # for i,row in gdf01.iterrows():
    #     if row['TBID'] not in tbid1:
    #         gdf0 = gdf0[gdf0['TBID']!=row['TBID']]
    #         print(f'删除TBID{row["TBID"]},ID{row["ID"]}')
    #         cnt += 1
    # ed_time = dt.now()
    # spd_time = ed_time - st_time
    # print(f'删除{cnt}个图斑，长度{len(gdf0)}，用时{spd_time} s')

    # # 修改图斑
    # st_time = dt.now()
    # cnt = 0
    # for i,row in gdf1[gdf1['mode'] == 1].iterrows():
    #     tbid = row['TBID']
    #     gdf0.loc[gdf0['TBID']==tbid,'geometry'] = row['geometry']
    #     cnt += 1
    # ed_time = dt.now()
    # spd_time = ed_time - st_time
    # print(f'修改{cnt}个图斑，长度{len(gdf0)}，用时{spd_time} s')

    # # 新增图斑
    # st_time = dt.now()
    # gdf12 = gdf1[gdf1['mode'] == 2]
    # st_idx = gdf0.index.max() + 1
    # gdf12.index = np.arange(st_idx,st_idx+len(gdf12))
    # gdf0 = pd.concat([gdf0,gdf12])
    # ed_time = dt.now()
    # spd_time = ed_time - st_time
    # print(f'新增{len(gdf12)}个图斑，长度{len(gdf0)}，用时{spd_time} s')

    # # 输出
    # gdf0 = gdf0.loc[:,['area','PSHSJ','YZLX','ID','status','reserve1','reserve2','TBID','geometry']]
    # for c in ['ID','status','reserve1','reserve2']:
    #     gdf0[c] = gdf0[c].astype('int')
    # gdf0.to_file(outfile,encoding='utf-8')

    changes = gdf1[gdf1['mode']>0]
    changes = changes.loc[:,['area','PSHSJ','YZLX','ID','status','reserve1','reserve2','TBID','geometry']]
    for c in ['ID','status','reserve1','reserve2']:
        changes[c] = changes[c].astype('int')
    changes.to_file(outfile.replace('.shp','_修改新增部分.shp'),encoding='utf-8')

