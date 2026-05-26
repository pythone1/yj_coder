import cv2
from segment_relations import *

# 待分割区县及保存路径
QX = '江苏省_泰州市_高港区' 
SAVEPATH = f'Q:\\项目数据\\江苏省一池一档水产养殖基本情况普查项目\\图像分割\\分割结果\\{QX}'
os.makedirs(SAVEPATH,exist_ok=True)  
# 分割影像：天地图0.5米
rgbpath = r'Q:\项目数据\江苏省一池一档水产养殖基本情况普查项目\图像分割\准备数据\d5m天地图影像'
_,ROWS,COLS,_ = imgpro.getGeoInfo(f'{rgbpath}\\{QX}.tif')

if __name__ == '__main__':
    ''' load mask generator '''
    device_ids = [0]    # gpu id list
    window_size = 480 * 4   # SAM输入尺寸
    points_interval = 15 * 4 # SAM每边点数间隔
    points_per_side = int(window_size / points_interval) # SAM每边点数
    print(f'points per side {points_per_side}')

    SAM_ARGS['points_per_side'] = points_per_side
    mask_generator = load_mask_generator(MODEL_PATH, device_ids, MODEL_TYPE, SAM_ARGS) # load SAM model

    ''' segmentation and selection'''
    # 总路径
    datapath = r'Q:\项目数据\江苏省一池一档水产养殖基本情况普查项目\图像分割\准备数据'    
    # 分割影像：天地图0.5米
    rgbpath = f'{datapath}\\d5m天地图影像'
    # 0.5米天地图矢量地图
    tdtvcpath = f'{datapath}\\d5m天地图矢量地图'
    # 时序提取水域：哨兵二号-ndwi为水的概率
    ndwipath = f'{datapath}\\哨兵二号_ndwigt0rat_重投影'
    # osm水系
    osmpath = f'{datapath}\\江苏省各区县osm水系矢量'
    # 建筑掩码：1米土地覆被分类数据集，code=6
    lcpath = f'{datapath}\\1m土地覆被分类_重投影'
    # 区县500m
    cntypath = f'{datapath}\\江苏省各区县'
    # 分割结果保存路径
    savepath = SAVEPATH
    # os.makedirs(savepath, exist_ok=True)
    # 运行日志-记录时间
    logfile = f'{savepath}\\{QX}.txt'
    # # 当前程序分割范围
    st_x0,st_y0 = 0,0
    ed_x0,ed_y0 = COLS,ROWS

    # 遍历文件分割
    rgbfiles = glob.glob(f'{rgbpath}\\{QX}.tif')

    with open(logfile,'a') as f:
        for rgbfile in rgbfiles:
            cntyname = os.path.basename(rgbfile)[0:-4]
            osmfile1 = glob.glob(f'{osmpath}\\*waterway_*{cntyname}*.gpkg')[0] # 河流
            osmfile2 = glob.glob(f'{osmpath}\\*water_*{cntyname}*.gpkg')[0] # 湖泊
            cntyfile = f'{cntypath}\\{cntyname}.gpkg' # 区县边界
            # 统一投影
            wgdf1 = gpd.read_file(osmfile1).to_crs('epsg:3857')
            wgdf2 = gpd.read_file(osmfile2).to_crs('epsg:3857')
            cnty = gpd.read_file(cntyfile).to_crs('epsg:3857')

            r0,c0 = ed_y0,ed_x0 # 行列数
            w0,st0 = 8515,6515 # 分块大小和步长
            for n in range(st_x0,c0,st0):
                w2 = min(w0,c0-n)
                for m in range(st_y0,r0,st0):
                    w1 = min(w0,r0-m)
                    drange = [n,m,w2,w1] # 当前读取范围（行列号）
                    filename = f'{os.path.basename(rgbfile)[0:-4].split("_")[-1]}{os.path.basename(rgbpath).split("天")[0]}_x{n}_y{m}'
                    print(filename)
                    f.write(f'\n{filename}: ') # 写日志，记录处理图像
                    f.flush()
                    # 分块地理范围
                    geotrans,rows,cols,epsg = imgpro.getGeoInfo(rgbfile)
                    roi = createBounds2(geotrans,drange,epsg=epsg)
                    roi.to_file(f'{savepath}/{filename}_范围.gpkg')
                    if not roi.geometry.intersects(cnty.geometry)[0]:
                        print(f'当前分块不在 {cntyname} 范围内')
                        continue

                    bounds = roi.total_bounds.tolist() # 当前读取范围（经纬度坐标）
                    
                    # 创建渔网-辅助后续人工编辑
                    if not os.path.exists(f'{savepath}/{filename}_fishnet300m.gpkg'):
                        fishnet = createFishnet(bounds,interval=300,epsg=epsg)
                        fishnet.to_file(f'{savepath}/{filename}_fishnet300m.gpkg')
                    
                    # segmentation
                    if not os.path.exists(f'{savepath}/{filename}_分割.gpkg'):
                        st_time = time.time()
                        # 天地图影像
                        geotif = imgpro.geotiffread(rgbfile,drange=drange)
                        mask_gdf = segmentgeotif(geotif, mask_generator, window_size=window_size) # 分割
                        mask_gdf.geometry = mask_gdf.geometry.buffer(1 / 100)  # 避免多边形自相交问题
                        mask_gdf = mask_gdf.to_crs('epsg:32650')
                        f.write(f'分割{round(time.time() - st_time,2)}s, ') # 写日志，记录分割用时
                        f.flush()
                        mask_gdf.to_file(f'{savepath}/{filename}_分割.gpkg') #  保存分割结果
                        
                    
                    # 去低得分
                    if not os.path.exists(f'{savepath}/{filename}_分割_去低得分.gpkg'):
                        mask_gdf = mask_gdf[mask_gdf['st_score'] > 0.9]
                        mask_gdf['area'] = mask_gdf.geometry.area
                        mask_gdf = mask_gdf[mask_gdf['area']>(0.3*666.6667)]
                        mask_gdf.to_file(f'{savepath}/{filename}_分割_去低得分.gpkg')
                    
                    # nms去重
                    if not os.path.exists(f'{savepath}/{filename}_分割_去低得分_去重.gpkg'):
                        if len(mask_gdf) == 0:
                            continue 
                        st_time = time.time()
                        mask_gdf = filterNms(mask_gdf, scfield='st_score', threshold=0.7)
                        print(f'nms used {time.time() - st_time} seconds, and {len(mask_gdf)} polygons remainded')
                        f.write(f'去重{round(time.time() - st_time,2)}s, ')
                        f.flush()
                        mask_gdf.to_file(f'{savepath}/{filename}_分割_去低得分_去重.gpkg')
                    else:
                        mask_gdf = gpd.read_file(f'{savepath}/{filename}_分割_去低得分_去重.gpkg')

                    # 根据内外轮廓水域分布筛选有包含关系的图斑
                    ndwifile = os.path.join(ndwipath,cntyname+'.tif')
                    maskfile1 = os.path.join(lcpath,cntyname+'.tif') # 建筑掩码
                    maskfile2 = os.path.join(tdtvcpath,cntyname+'.tif') # 天地图矢量掩码
                    if os.path.exists(ndwifile) and os.path.exists(maskfile2):
                        # 去非水域-先全部用哨兵二判断一次
                        if not os.path.exists(f'{savepath}/{filename}_分割_去低得分_去重_去非水.gpkg'):
                            mask_gdf = mask_gdf.to_crs(f'epsg:{epsg}')
                            mask_gdf['wt_judge'] = 'nan' # 记录根据什么数据判定为水域的
                            st_time = time.time()
                            drange = getGeotifDRange(ndwifile,bounds)
                            geotif = imgpro.geotiffread(ndwifile,drange)
                            waters1 = geotif.dataarray # 根据ndwi取水域
                            waters1[waters1>=0.25] = 1
                            waters1[waters1<0.25] = 0
                            geotif = imgpro.geotiffread(maskfile1,drange)
                            buildings = geotif.dataarray # 根据建筑掩码剔除噪声
                            waters1[buildings==1] = 0
                            waters1[buildings==6] = 0
                            geotrans = geotif.geo_transform
                            s2_reserves = filterWater(mask_gdf,waters1,geotrans,threshold=0.1)
                            idx = mask_gdf[s2_reserves].index
                            mask_gdf.loc[idx,'wt_judge'] = 's2_water' # 记录为根据哨兵二号判定为水域
                
                            # 去非水域-对哨兵判定无水且5亩以下的天地图矢量再判定一次
                            drange = getGeotifDRange(maskfile2,bounds)
                            geotif = imgpro.geotiffread(maskfile2,drange)
                            data = geotif.dataarray
                            data = cv2.cvtColor(data, cv2.COLOR_RGB2HSV)[:,:,0]
                            waters2 = np.zeros_like(data)
                            waters2[data == 108] = 1 # 天地图矢量提取水域
                            waters2 = cv2.resize(waters2,(waters1.shape[1],waters1.shape[0]))
                            s2_nserves = mask_gdf[(~s2_reserves) & (mask_gdf['area']<5*666.6667)] 
                            tdt_reserves = filterWater(s2_nserves,waters2,geotrans,threshold=0.5) 
                            idx = mask_gdf[(~s2_reserves) & (mask_gdf['area']<5*666.6667)][tdt_reserves].index
                            mask_gdf.loc[idx,'wt_judge'] = 'tdt_water'
                            mask_gdf = mask_gdf[mask_gdf['wt_judge']!='nan']
                            print(f'filter water used {time.time() - st_time} seconds, and {len(mask_gdf)} polygons remainded')
                            f.write(f'去非水{round(time.time() - st_time,2)}s, ')
                            f.flush()
                            mask_gdf.to_file(f'{savepath}/{filename}_分割_去低得分_去重_去非水.gpkg')  

                        # 去包含-基于哨兵二号提取水域和天地图5亩以下水域判断
                        if not os.path.exists(f'{savepath}/{filename}_分割_去低得分_去重_去非水_去包含.gpkg'):
                            st_time = time.time()
                            data[data!=108]=0
                            data[data==108]=1
                            data = cv2.morphologyEx(data,cv2.MORPH_CLOSE,kernel=np.ones((3,3),np.uint8))
                            # 保存天地图矢量
                            imgpro.geotiffwrite(f'{savepath}/{filename}_天地图矢量提取水域.tif',data,geotif.geo_transform,geotif.projection,datatype="UINT8")
                            imgpro.createShpfile_from_geotiff(f'{savepath}/{filename}_天地图矢量提取水域.gpkg',f'{savepath}/{filename}_天地图矢量提取水域.tif')
                            tdtwaters = gpd.read_file(f'{savepath}/{filename}_天地图矢量提取水域.gpkg')
                            tdtwaters['area'] = tdtwaters.to_crs('epsg:32650').geometry.area
                            tdtwaters = tdtwaters[tdtwaters['area']<5*666.66667]
                            if len(tdtwaters)>0:
                                geoms = [shapes for shapes in tdtwaters.geometry]
                                tdtwaters = features.rasterize(geoms, out_shape=waters1.shape, 
                                                            all_touched=False,transform=(geotrans[1], 0, geotrans[0], 0, geotrans[5], geotrans[3]),
                                                            default_value=1, fill=0)
                                waters1[tdtwaters==1] = 1
                            mask_gdf = filterOutInn(mask_gdf,waters1,geotrans) # 去包含
                            print(f'filter overlapped used {time.time() - st_time} seconds, and {len(mask_gdf)} polygons remainded')
                            f.write(f'去包含{round(time.time() - st_time,2)}s, ')
                            f.flush()
                            mask_gdf.to_file(f'{savepath}/{filename}_分割_去低得分_去重_去非水_去包含.gpkg') 

                           
                    # 去河湖
                    if not os.path.exists(f'{savepath}/{filename}_分割_去低得分_去重_去非水_去包含_去河湖.gpkg'): 
                        mask_gdf = mask_gdf.to_crs('epsg:3857').reset_index(drop=True)
                        st_time = time.time()
                        # osm去除
                        idx1 = gpd.sjoin(mask_gdf,wgdf1).index.values
                        idx2 = gpd.sjoin(mask_gdf,wgdf2).index.values
                        idx1 = np.unique(np.hstack((idx1,idx2)).flatten())
                        flags = np.array([True]*len(mask_gdf))
                        flags[idx1] = False
                        mask_gdf = mask_gdf[flags]
                        # shape去除
                        mask_gdf = mask_gdf.to_crs('epsg:32650')
                        if len(mask_gdf)>0:
                            mask_gdf = filterShape(mask_gdf)
                        f.write(f'去河湖{round(time.time() - st_time,2)}s')
                        f.flush()
                        mask_gdf.to_file(f'{savepath}/{filename}_分割_去低得分_去重_去非水_去包含_去河湖.gpkg')
                
    f.close()
                    