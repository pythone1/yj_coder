import os,glob

import geopandas as gpd
import pandas as pd
import folium

def add_tian_di_tu_layers(map_object):
    tian_di_tu_normal_map = ("https://t6.tianditu.gov.cn/img_w/wmts"
                         "?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0"
                         "&LAYER=img&STYLE=default&TILEMATRIXSET=w"
                         "&FORMAT=tiles&TILECOL={x}&TILEROW={y}"
                         "&TILEMATRIX={z}&tk=5625113a2addc9a7594d0fffe3811311")

    # 天地图注记图层的URL模板
    tian_di_tu_zhuji = ("https://t6.tianditu.gov.cn/cia_w/wmts"
                        "?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0"
                        "&LAYER=cia&STYLE=default&TILEMATRIXSET=w"
                        "&FORMAT=tiles&TileCol={x}&TileRow={y}"
                        "&TileMatrix={z}&tk=5625113a2addc9a7594d0fffe3811311")
    
    for name, url in [("天地图影像", tian_di_tu_normal_map), ("天地图注记", tian_di_tu_zhuji)]:
        folium.TileLayer(
            tiles=url,
            attr=name,
            name=name,
            overlay=name,
            control=False
        ).add_to(map_object)

def createCTMap(ct,xzq):
    '''
    创建池塘地图
    '''
    try:
        minx,miny,maxx,maxy = xzq.total_bounds
    except:
        minx,miny,maxx,maxy = xzq.bounds
    centroid_coords = [(miny+maxy)/2,(minx+maxx)/2]
    m = folium.Map(location=centroid_coords, zoom_start=15,tiles=None)
    add_tian_di_tu_layers(m)

    style_function = lambda x: {
        'fillColor': '#transparent', 
        'color': '#00FFFF',  # 青色
        'weight': 1,
    }
    folium.GeoJson(
        ct,
        style_function=style_function,
        name='池塘',
    ).add_to(m)

    style_function = lambda x: {
        'fillColor': '#transparent',
        'color': '#FFFF00',  # 黄色
        'weight': 2,
    }
    folium.GeoJson(
        xzq[xzq['CT']=='是'],
        style_function=style_function,
        name='位于池塘范围内风电项目',
    ).add_to(m)

    style_function = lambda x: {
        'fillColor': '#transparent',
        'color': '#FF0000',  # 红色
        'weight': 2,
    }
    folium.GeoJson(
        xzq[xzq['CT']=='否'],
        style_function=style_function,
        name='其他风电项目',
    ).add_to(m)

    folium.LayerControl().add_to(m)

    return m

if __name__ == '__main__':
    pth = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\其他\风电项目\0113科教处 第二批陆上风电征求意见电子版资料'
    os.chdir(pth)

    # g_list = []
    # files = glob.glob("*.shp")
    # for f in files:
    #     gdf = gpd.read_file(f).to_crs('epsg:4490')
    #     gdf['城市'] = f[0:3]
    #     g_list.append(gdf)
    # gdf = pd.concat(g_list,ignore_index=True)
    # gdf.to_file(r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\其他\风电项目\0113科教处 第二批陆上风电征求意见电子版资料\风机项目点位.shp',encoding='utf-8')
    # print('合并完成')

    fjfile = '风机项目点位.shp'
    gdf = gpd.read_file(fjfile)

    ct_file = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\其他\风电项目\江苏水产种质资源区.shp'
    ct = gpd.read_file(ct_file).to_crs('epsg:32650')
    ct.geometry = ct.buffer(1000)
    ct = ct.to_crs('epsg:4490')

    sjoins = gpd.sjoin(ct,gdf)
    gdf['CT'] = '否'
    gdf.loc[sjoins['index_right'].values,'CT'] = '是'
    gdf.to_file('风电项目点位_是否位于水产种质资源区buf1000.shp',encoding='utf-8')
    sjoins.to_file('风机项目关联水产种质资源区buf1000.shp',encoding='utf-8')
    
    
    # # 上图
    # fjfile = '风电项目点位_是否位于池塘.shp'
    # fj = gpd.read_file(fjfile)

    # ctfile = '风机项目关联池塘.shp'
    # ct = gpd.read_file(ctfile)

    # m = createCTMap(ct,fj)
    # m.save(r'风电项目及关联池塘.html')
