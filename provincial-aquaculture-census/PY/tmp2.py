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
        'color': '#FFFF00',  # 黄色
        'weight': 1,
    }
    folium.GeoJson(
        ct,
        style_function=style_function,
        name='渔光一体',
    ).add_to(m)

    style_function = lambda x: {
        'fillColor': '#transparent',
        'color': '#000000',  # 黑色
        'weight': 2,
    }
    folium.GeoJson(
        xzq,
        style_function=style_function,
        name='行政区划',
    ).add_to(m)

    folium.LayerControl().add_to(m)

    return m

if __name__ == '__main__':
    pth = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\其他\光伏板\PV-20250113T045225Z-001\市光伏板_withinPV'
    outpth = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\其他\光伏板\PV-20250113T045225Z-001\市光伏板_withinPV_html'
    os.makedirs(outpth,exist_ok=True)
    os.chdir(pth)  

    file0 = r'S:\通用数据\天地图_2021公众版江苏省行政区划\JiangSu_XZQH.shp' 
    gdf0 = gpd.read_file(file0)

    # 上图
    files = glob.glob('*.shp')
    for f in files:
        gf = gpd.read_file(f)
        shi = gdf0[gdf0['市']==f[0:-4]]
        m = createCTMap(gf,shi)
        m.save(f'{outpth}\\{f[0:-4]}.html')
    
