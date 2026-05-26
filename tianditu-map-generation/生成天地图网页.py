
import folium

def createBaseMap(location,zoom_start,tilesname='天地图影像图',annotate=False):
    '''
    功能：创建常规地图
    返回：地图对象
    location: 初始中心坐标[纬度,经度]
    zoom_start: 初始层级
    tilesname：底图名称，可选参数详见tileslist
    annotate：bool类型，选择是否添加注记（只对天地图有效，其他地图默认将底图与注记一起切片发布）
    '''
    tilesdict = {
        '天地图影像图':'http://t7.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=img&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=',
        '天地图矢量图':'http://t7.tianditu.gov.cn/vec_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=vec&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=',
        '天地图地形图':'http://t7.tianditu.gov.cn/ter_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ter&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=',
        '天地图影像注记':'http://t7.tianditu.gov.cn/cia_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=cia&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=',
        '天地图矢量注记':'http://t7.tianditu.gov.cn/cva_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=cva&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=',
        '天地图地形注记':'http://t7.tianditu.gov.cn/cta_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=cta&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=',
        '高德地图影像图':'http://webst02.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}',
        '高德地图矢量图':'https://wprd01.is.autonavi.com/appmaptile?x={x}&y={y}&z={z}&lang=zh_cn&size=1&scl=1&style=7',
        '高德地图街道图':'https://wprd01.is.autonavi.com/appmaptile?x={x}&y={y}&z={z}&lang=zh_cn&size=1&scl=1&style=8&ltype=11',
        '腾讯地图':'https://rt0.map.gtimg.com/tile?z={z}&x={x}&y={-y}',
        '智图彩色图':'http://map.geoq.cn/ArcGIS/rest/services/ChinaOnlineCommunity/MapServer/tile/{z}/{y}/{x}',
        '智图暖色图':'http://map.geoq.cn/ArcGIS/rest/services/ChinaOnlineStreetWarm/MapServer/tile/{z}/{y}/{x}',
        '智图灰色图':'http://map.geoq.cn/ArcGIS/rest/services/ChinaOnlineStreetGray/MapServer/tile/{z}/{y}/{x}',
        '智图蓝黑图':'http://map.geoq.cn/ArcGIS/rest/services/ChinaOnlineStreetPurplishBlue/MapServer/tile/{z}/{y}/{x}',
        '智图行政区划图':'http://thematic.geoq.cn/arcgis/rest/services/ThematicMaps/administrative_division_boundaryandlabel/MapServer/tile/{z}/{y}/{x}',
        '智图水系图':'http://thematic.geoq.cn/arcgis/rest/services/ThematicMaps/WorldHydroMap/MapServer/tile/{z}/{y}/{x}',
        '智图灰色街道图':'http://thematic.geoq.cn/arcgis/rest/services/StreetThematicMaps/Gray_OnlySymbol/MapServer/tile/{z}/{y}/{x}',
        '智图暖色街道图':'http://thematic.geoq.cn/arcgis/rest/services/StreetThematicMaps/Warm_OnlySymbol/MapServer/tile/{z}/{y}/{x}',    
        'OpenStreetMap':'OpenStreetMap'
    }

    newmap = folium.Map(
        location=location,
        zoom_start=zoom_start,
        tiles=tilesdict[tilesname],
        attr=tilesname,
        control_scale=False,
        crs='EPSG3857'
    )
    
    if annotate and ('天地图' in tilesname):
        annotationname = tilesname[0:-1] + "注记"
        folium.TileLayer(tiles=tilesdict[annotationname],
            attr=annotationname,
        ).add_to(newmap)

    return newmap

if __name__ == '__main__':
    cmap = createBaseMap([31.88,121.74],12,'天地图影像图',annotate=False)    
    cmap.save(r'D:\tdt_image.html')