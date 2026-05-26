from segment_relations import *

if __name__ == '__main__':
    ''' prepare data '''
    # 总路径
    datapath = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\图像分割\准备数据'    
    # 分割影像：天地图0.5米
    rgbpath = f'{datapath}\\d5m天地图影像' # qgis+天地图在线地图下载
    # 0.5米天地图矢量地图
    tdtvcpath = f'{datapath}\\d5米天地图矢量地图'
    # 时序提取水域：哨兵二号-ndwi为水的概率，通过哨兵二号官网下载
    ndwipath1 = f'{datapath}\\哨兵二号_ndwigt0rat'
    ndwipath2 = f'{datapath}\\哨兵二号_ndwigt0rat_重投影'
    # 建筑掩码：1米土地覆被分类数据集，code=6。从dynamicworld数据集下载
    lcpath1 = f'{datapath}\\1m土地覆被分类'
    lcpath2 = f'{datapath}\\1m土地覆被分类_重投影'
    # 区县500m
    cntypath = f'{datapath}\\江苏省各区县' # 天地图_2021公众版江苏省行政区划
    cntyfiles = glob.glob(f'{cntypath}\\*江苏省_泰州市_高港区.gpkg')

    # 哨兵时序水域、建筑投影到3857,并裁剪到天地图范围
    for cntyfile in cntyfiles:
        basename = os.path.basename(cntyfile).replace('.gpkg','.tif')
        ndwifile1 = os.path.join(ndwipath1,basename)
        ndwifile2 = os.path.join(ndwipath2,basename)
        lcfile1 = os.path.join(lcpath1,basename)
        lcfile2 = os.path.join(lcpath2,basename)
        tdtfile = os.path.join(rgbpath,basename)
        if os.path.exists(tdtfile) and (not os.path.exists(ndwifile2)) and (not os.path.exists(lcfile2)):
            print(cntyfile)
            data_uni_run4(ndwifile1,ndwifile2,lcfile1,lcfile2,tdtfile)
