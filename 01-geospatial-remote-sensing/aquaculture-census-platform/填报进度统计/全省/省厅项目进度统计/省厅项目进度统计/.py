"""
项目名称: aquaculture-census-platform
技术领域: 01-geospatial-remote-sensing
模块说明: .py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

import os,glob

import geopandas as gpd

from CTXXTBYD import *

if __name__ == '__main__':
    # 数据目录
    pth = r'F:\工作\江苏省农业厅渔业资源调查\进度统计表\全省进度'
    os.chdir(pth)

    # ctxxfile = '池塘信息-宿迁市.xlsx'
    ctxxfile = r'F:\工作\江苏省农业厅渔业资源调查\进度统计表\全省进度\20250307'
    ctfile0 = r'F:\工作\江苏省农业厅渔业资源调查\进度统计表\全省进度\江苏省池塘图斑03061700.gpkg'
    deletes = r'F:\工作\江苏省农业厅渔业资源调查\图斑修改内容汇总\删除需求图斑\20250304'
    # deletes = None
    roifile = r'F:\工作\python\省厅项目进度统计\JiangSu_XZQH.shp' # 统计范围
    dfxzqfile = r'F:\工作\python\省厅项目进度统计\所有地方行政区划.gpkg' # 用于判别图斑属于哪个地方区划
    prefixlktable = r'F:\工作\python\省厅项目进度统计\江苏省城市缩写-调格式.xlsx' # 图斑编号前缀查找表
    ownshplktable = r'F:\工作\python\省厅项目进度统计\图斑权属调整.xlsx' # 地方上报、双方确认的图斑权属调整

    # 统计范围
    shi = ''
    qx = ''
    name = shi+qx
    roi = gpd.read_file(roifile)
    if roifile.endswith('JiangSu_XZQH.shp'):        
        if (len(name)<=4) & (len(name)>0):
            roi = roi[roi['市']==name]
        elif len(name)>4:
            roi = roi[roi['NAME']==name]
    else:
        if (len(name)<=4) & (len(name)>0):
            roi = roi[roi['地方市']==name]
        elif len(name)>4:
            roi = roi[roi['DFNAME']==name]

    # 池塘图斑
    if roifile.endswith('JiangSu_XZQH.shp'):
        ct_file = f"{os.path.basename(ctfile0).split('.')[0]}_平台_{name}.gpkg"
        if os.path.exists(ct_file):
            ct = gpd.read_file(ct_file)
            roi = roi.to_crs(ct.crs)
        else:
            ct = gpd.read_file(ctfile0)
            ct = ct.rename(columns = {
                'tbid':'TBID',
                'id':'ID'
            })
            # 筛选图斑
            lkt = pd.read_excel(prefixlktable)
            if len(name)>0:
                prefix = lkt.loc[lkt['NAME']==name,'市区缩写'].values[0]
                ct = ct[ct['TBID'].str.startswith(prefix)] 
            # 合并市、区县名称
            ct['市区缩写'] = ct['TBID'].str.split(',',expand=True)[0]            
            ct = pd.merge(ct,lkt.loc[:,['市','区县','市区缩写']],how='left',on='市区缩写')
            # # 按地方上报、双方确认的内容调整图斑权属 ——取消
            # ownshplkt = pd.read_excel(ownshplktable)
            # ct = reallocatePolygons(ct,ownshplkt)
            ct.to_file(ct_file,encoding='utf-8',driver='GPKG')   
    else:
        ct_file = f"{os.path.basename(ctfile0).split('.')[0]}_地方_{name}.gpkg"
        if os.path.exists(ct_file):
            ct = gpd.read_file(ct_file)
            roi = roi.to_crs(ct.crs)
        else:
            ct = gpd.read_file(ctfile0)
            print('reading ctfile0')
            roi = roi.to_crs(ct.crs)
            ct = gpd.sjoin(ct,roi,how='inner')
            print('ctfile0 sjoin roi')
            ct = ct.drop_duplicates(subset=['TBID'])
            # # 按地方上报、双方确认的内容调整图斑权属 ——取消
            # ownshplkt = pd.read_excel(ownshplktable)
            # ct = reallocatePolygons(ct,ownshplkt)
            ct.to_file(ct_file,encoding='utf-8',driver='GPKG')    
            print('write ct_file')
    
    # 池塘图斑赋填报状态
    out_point = f'{ctxxfile.split(".")[0]}-{name}-填报点.gpkg'
    out_polygons = f'{ctxxfile.split(".")[0]}-{name}-池塘图斑.gpkg'
    if os.path.exists(out_point) & os.path.exists(out_polygons):
        sjoins = gpd.read_file(out_point)
        polygons = gpd.read_file(out_polygons)
    else:
        sjoins,polygons,pk = mergeData(ctxxfile,ct_file,dels_file=deletes)

        # 写出点矢量
        st_time = datetime.now()
        sjoins.to_file(out_point,encoding='utf-8', driver='GPKG')
        sjoins['池塘id'] = sjoins.index.values        
        ed_time = datetime.now()
        spd_time = (ed_time - st_time).total_seconds()
        print(f"写出点矢量：{np.round(spd_time/60,0)} 分钟")

        # 写出面矢量
        st_time = datetime.now()
        polygons.drop('ID',axis=1).to_file(out_polygons,encoding='utf-8', driver='GPKG')
        ed_time = datetime.now()
        spd_time = (ed_time - st_time).total_seconds()
        print(f"写出面矢量：{np.round(spd_time/60,0)} 分钟")


    # 按字段统计填报进度
    # TBJDTJ04(polygons,['地方市','地方区县','镇名称','村名称'],outfile=f"{ctxxfile.split('.')[0]}-{name}-填报图斑统计（按校对状态）.xlsx")
    TBJDTJ04(polygons,['市','区县'],outfile=f"{ctxxfile.split('.')[0]}-{name}-填报图斑统计（按校对状态）.xlsx")

    # 未填报图斑清单对应地方镇
    polygons = polygons[polygons['Ndel']] # 剔除待删除
    polygons = polygons[polygons['填报状态'] == '未填报']
    # exportTablesByFieldsAndDFXZQ(polygons,
    #                              groupby=['市','区县'],
    #                              outpth = f"{ctxxfile.split('.')[0]}-{name}-填报图斑统计（按校对状态）-未填报图斑对应地方行政区划.xlsx",
    #                              dfxzqfile=dfxzqfile,
    #                              fields=['TBID'])