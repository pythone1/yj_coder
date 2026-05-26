import psycopg2
from shapely import wkt

def selectPgItems(config,strsql):
    '''
    查找影像文件
    :param config: dict 包含程序运行参数
    :param strsql: str sql查询语句
    :return results: list[cell] 查询结果
    '''
    host = config['host']
    port = config['port']
    user = config['user']
    password = config['password']
    database = config['database']

    conn = psycopg2.connect('host={} port={} user={} password={} dbname={}'.format(host,port,user,password,database))
    cur = conn.cursor()
    cur.execute(strsql)
    results = cur.fetchall()
    colnames = [i.name for i in cur.description]
    cur.close()

    # 查询结果合并为pd.DataFrame对象
    # df = pd.DataFrame()
    # for i in range(len(results)):
    #     r = results[i]
    #     for j in range(len(r)):
    #         df.loc[i,colnames[j]] = r[j]

    return results,colnames

def insertItems2Geotable(df,tablename,config):
    '''
    向pgsql中的数据表插入一条记录
    :param df: pd.DataFrame 待插入内容
    :param tablename: str 表名
    :param config: dict 包含pgsql连接参数
    :return:
    '''
    # connect to pgsql
    host = config['host']
    port = config['port']
    user = config['user']
    password = config['password']
    dbname = config['database']
    conn = psycopg2.connect('host={} port={} user={} password={} dbname={}'.format(host, port, user, password,dbname))
    cur = conn.cursor()

    # insert items
    columns = list(df.columns)
    for i in range(len(df)):
        values = list(df.loc[i,:])
        columns1 = ''
        values1 = '\''
        for j,c in enumerate(columns):
            if c not in ['center_lon','center_lat','geometry','cld_pct']:
                columns1 = columns1 + c + ','
                print(values[j])
                values1 = values1 + str(values[j]) + '\',\''
        columns1 = columns1[0:-1]
        values1 = values1[0:-2]
        if columns1 not in ['cld_pct']:
            cur.execute("INSERT INTO {0} ({1},center_lon,center_lat,cld_pct,geometry)"
                        "VALUES({2},{3},{4},{5},ST_GeometryFromText('SRID=4326;{6}'))".format(
                tablename, columns1, values1, df.loc[i, 'center_lon'], df.loc[i, 'center_lat'],
                df.loc[i, 'cld_pct'],wkt.loads(df.loc[i, 'geometry'])))
        else:
            cur.execute("INSERT INTO {0} ({1},center_lon,center_lat,image_gsd,geometry) "
                        "VALUES({2},{3},{4},{5},ST_GeometryFromText('SRID=4326;{6}'))".format(
            tablename, columns1, values1, df.loc[i, 'center_lon'], df.loc[i, 'center_lat'], df.loc[i, 'image_gsd'],
            df.loc[i, 'geometry']))
        conn.commit()
        cur.close()

# conn = psycopg2.connect('host=10.10.10.148 port=5432 user=postgres password=tech5d_ndww dbname=geodatabase')
# cur = conn.cursor()
#
# tablename = 'geomtest'
# imginfo = dict()
# imginfo['platform'] = 'sentinel1'
# imginfo['sensor'] = 'csar'
# imginfo['band_name'] = 'vh,vv'
# imginfo['product_level'] = 'DB'
# imginfo['product_level'] = 'DB'
# imginfo['geometry'] = 'POLYGON ((119.23056763945362 34.743216139894514, 119.46613427903083 34.743216139894514, 119.46910860528806 34.63554552938069, 119.23056763945362 34.63911472088944, 119.23056763945362 34.743216139894514))'
# columns = tuple(imginfo.keys())
# values = tuple(imginfo.values())

# v = 'product_level'
# cur.execute("INSERT INTO geomtest(sensor) VALUES('msi')")
# cur.execute("ALTER TABLE geomtest ADD COLUMN IF NOT EXISTS {} varchar".format(v))
# cur.execute("INSERT INTO geomtest (geom) VALUES (ST_GeometryFromText('SRID=4326;{}'))".format(imginfo['geometry']))
# conn.commit()
# cur.close()

# strsql = "ALTER TABLE {} ADD COLUMN IF NOT EXISTS {} varchar"
# for col in columns:
#     sqlstr = "ALTER TABLE {} ADD COLUMN IF NOT EXISTS {} varchar".format(tablename,col)
#     cur.execute(strsql)
#     results = cur.fetchall()
#     cur.close()


# ALTER TABLE table_name ADD COLUMN IF NOT EXISTS column_name column_type;
#
# INSERT INTO global_points (name, location) VALUES
# ('London', ST_GeographyFromText('SRID=4326; POINT(-72.1235 42.3521)'));
#
#
# sqlstr = """INSERT INTO geomtest ()"""

