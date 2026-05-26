import os,glob

import geopandas as gpd

from CTXXTBYD import *

if __name__ == '__main__':
    # 数据目录
    pth = r'E:\全省养殖池溏上图入库普查\填报进度统计\苏州市\20250427'
    os.chdir(pth)

    ctxxfile = '苏州市'
    ctfile0 = r'E:\全省养殖池溏上图入库普查\填报进度统计\苏州市\20250427\20250425江苏省池塘图斑.gpkg'
    # deletes = r'E:\江苏省养殖池塘上图入库项目\进度统计\删除需求图斑\20250417'
    deletes = None
    roifile = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\图斑汇总\20241225江苏省池塘图斑\20250122江苏省池塘顺延编号\JiangSu_XZQH.shp'
    # roifile = r'E:\python\省厅项目进度统计\所有地方行政区划.gpkg' # 统计范围
    dfxzqfile = r'E:\全省养殖池溏上图入库普查\PY\省厅项目进度统计\行政区划_新\所有地方行政区划_镇合并.gpkg' # 用于判别图斑属于哪个地方区划

    # 宝应
    # roifile = r'E:\python\省厅项目进度统计\行政区划_新\宝应县村级行政区划.gpkg' # 统计范围
    # dfxzqfile = r'E:\python\省厅项目进度统计\行政区划_新\宝应县村级行政区划.gpkg' # 用于判别图斑属于哪个地方区划
    #
    # # 宿城区
    # roifile = r'E:\python\省厅项目进度统计\行政区划_新\宿城区村级行政区划.gpkg' # 统计范围
    # dfxzqfile = r'E:\python\省厅项目进度统计\行政区划_新\宿城区村级行政区划.gpkg' # 用于判别图斑属于哪个地方区划

    # 清江浦区
    # roifile = r'E:\python\省厅项目进度统计\行政区划_新\所有地方行政区划.gpkg' # 统计范围
    # dfxzqfile = r'E:\python\省厅项目进度统计\行政区划_新\所有地方行政区划_镇合并.gpkg' # 用于判别图斑属于哪个地方区划

    prefixlktable = r'E:\python\省厅项目进度统计\江苏省城市缩写-调格式.xlsx' # 图斑编号前缀查找表
    ownshplktable = r'E:\python\省厅项目进度统计\图斑权属调整.xlsx' # 地方上报、双方确认的图斑权属调整

    # 统计范围
    shi = '苏州市'
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
            ct = ct.rename(columns = {
                'tbid':'TBID',
                'id':'ID'
            })
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


        try:
            sjoins.to_file(out_point,encoding='utf-8', driver='GPKG')
        except:
            chunk_size = 500000
            num_chunks = (len(sjoins) - 1) // chunk_size  # 计算需要拆分的份数（减去表头）
            t=chunk_size*num_chunks
            for i in range(num_chunks+1):
                # 获取当前分块的数据
                if i<=num_chunks:
                    start = i * chunk_size  # 从第二行开始（跳过表头）
                    end = start + chunk_size
                    chunk = sjoins.iloc[start:end]

                    # 将表头和当前分块数据合并
                    result = chunk
                else:
                    start = i * chunk_size
                    end = start + len(sjoins) - 1-t
                    chunk = sjoins.iloc[start:end]

                    # 将表头和当前分块数据合并
                    result = chunk
                result.to_file(f'{ctxxfile.split(".")[0]}-{name}-填报点{i}.gpkg',encoding='utf-8', driver='GPKG')

        
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
    # 按字段统计填报进度
    if roifile.endswith('JiangSu_XZQH.shp'):
        # 全省进度统计用
        # 按校对状态统计
        TBJDTJ04(polygons,
                 ['市','区县'],
                 outfile=f"{ctxxfile.split('.')[0]}-{name}-填报图斑统计（按校对状态）.xlsx",
                 subtotle=True)
        # 按填报状态统计
        TBJDTJ05(polygons,
                ['市','区县'],
                outfile=f"{ctxxfile.split('.')[0]}-{name}-填报图斑统计（按填报状态）.xlsx",
                subtotle=True)
        # 未填报图斑清单对应地方镇
        polygons = polygons[polygons['Ndel']] # 剔除待删除
        polygons = polygons[polygons['填报状态'] == '未填报']
        exportTablesByFieldsAndDFXZQ(polygons,
                                    groupby=['市','区县'],
                                    outpth = f"{ctxxfile.split('.')[0]}-{name}-填报图斑统计（按校对状态）-未填报图斑对应地方行政区划.xlsx",
                                    dfxzqfile=dfxzqfile,
                                    fields=['TBID'])
    else:
        # 地方统计到镇村用
        # 按校对状态统计
        TBJDTJ04(polygons,
                ['地方市','地方区县','镇名称','村名称'],
                outfile=f"{ctxxfile.split('.')[0]}-{name}-填报图斑统计（按校对状态）.xlsx",
                subtotle=False)
        # 按填报状态统计
        TBJDTJ05(polygons,
                ['地方市','地方区县','镇名称','村名称'],
                outfile=f"{ctxxfile.split('.')[0]}-{name}-填报图斑统计（按填报状态）.xlsx",
                subtotle=False)
    # # 地方统计到镇村用
    # # TBJDTJ04(polygons,
    # #          ['地方市','地方区县','镇名称','村名称'],
    # #          outfile=f"{ctxxfile.split('.')[0]}-{name}-填报图斑统计（按校对状态）.xlsx",
    # #          subtotle=True)
    # # 全省进度统计用
    # TBJDTJ04(polygons,
    #          ['市','区县'],
    #          outfile=f"{ctxxfile.split('.')[0]}-{name}-填报图斑统计（按校对状态）.xlsx",
    #          subtotle=True)
 
    # # # 未填报图斑清单对应地方镇
    # # polygons = polygons[polygons['Ndel']] # 剔除待删除
    # # polygons = polygons[polygons['填报状态'] == '未填报']
    # # exportTablesByFieldsAndDFXZQ(polygons,
    # #                              groupby=['市','区县'],
    # #                              outpth = f"{ctxxfile.split('.')[0]}-{name}-填报图斑统计（按校对状态）-未填报图斑对应地方行政区划.xlsx",
    # #                              dfxzqfile=dfxzqfile,
    # #                              fields=['TBID'])

    # TBJDTJ05(polygons,
    #          ['地方市','地方区县','镇名称','村名称'],
    #          outfile=f"{ctxxfile.split('.')[0]}-{name}-填报图斑统计（按填报状态）.xlsx",
    #          subtotle=True)