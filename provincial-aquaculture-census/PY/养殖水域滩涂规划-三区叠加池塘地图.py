from CTXXTBYD import *

def createCTMap(ct,sq,xzq):
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

    # 三区
    # c_list = ['#f00000','#ffff18','#6fff00']
    sf_list = [
        lambda x: {
            'fillOpacity': 0.5, 
            'color': '#f00000',
            'weight': 0,
        },
        lambda x: {
            'fillOpacity': 0.5, 
            'color': '#ffff18',
            'weight': 0,
        },
        lambda x: {
            'fillOpacity': 0.5, 
            'color': '#6fff00',
            'weight': 0,
        }
    ]
    typ_list = ['禁养区','限养区','养殖区']
    for i in range(3):
        typ = typ_list[i]
        folium.GeoJson(
            sq[sq['规划类']==typ],
            style_function=sf_list[i],
            name=typ,
        ).add_to(m)

    # 池塘图斑
    # c_list = ['#e41a1c','#20da26']
    sf_list = [
        lambda x: {
            'fillColor': '#transparent', 
            'color': '#e41a1c',
            'weight': 1,
        },
        lambda x: {
            'fillColor': '#transparent', 
            'color': '#20da26',
            'weight': 1,
        }
    ]
    typ_list = ['未填报','已填报养殖']
    for i in range(2):
        typ = typ_list[i]
        folium.GeoJson(
            ct[ct['填报状态']==typ],
            style_function=sf_list[i],
            name=typ,
        ).add_to(m)

    # 行政区
    style_function = lambda x: {
    'fillColor': '#transparent',
    'color': '#000000',  # 黑色
    'weight': 2,
    }
    folium.GeoJson(
        xzq,
        style_function=style_function,
        name='行政区',
    ).add_to(m)

    folium.LayerControl().add_to(m)

    return m

if __name__ == "__main__":
    file1 = r'S:\通用数据\全省水域滩涂养殖规划数据\规划图\无锡市\无锡市_123合并_宜兴市.shp'
    file2 = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\疑点和进度统计\无锡市宜兴市\池塘信息-20250120-20250120132743-无锡市宜兴市-池塘图斑赋疑点.json'
    file3 = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\按区县拆分池塘\无锡市_宜兴市\宜兴市行政区划.shp'

    sq = gpd.read_file(file1)
    ct = gpd.read_file(file2)
    xzq = gpd.read_file(file3)

    m = createCTMap(ct,sq,xzq)
    m.save(r'S:\项目数据\江苏省水产养殖滩涂规划修编项目\宜兴\池塘信息-20250120-叠加三区.html')