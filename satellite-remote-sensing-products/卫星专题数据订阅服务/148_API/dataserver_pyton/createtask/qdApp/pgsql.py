import psycopg2
import pandas as pd

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
    database = config['database']
    conn = psycopg2.connect('host={} port={} user={} password={} dbname={}'.format(host, port, user, password,database))
    cur = conn.cursor()

    # insert items
    columns = list(df.columns)
    for i in range(len(df)):
        values = list(df.loc[i,:])
        columns1 = ''
        values1 = '\''
        for j,c in columns:
            if c not in ['center_lon','center_lat','geometry']:
                columns1 = columns1 + c + ','
                values1 = values1 + values[j] + '\',\''
        columns1 = columns1[0:-1]
        values1 = values1[0:-2]
        cur.execute("INSERT INTO {0}({1},cld_pct,center_lon,center_lat,geometry) "
                    "VALUES({2},{3},{4},{5},ST_GeometryFromText('SRID=4326;{6}')))".format(
            tablename,columns1,values1,df.loc[i,'center_lon'],df.loc[i,'center_lat'],df.loc[i,'geometry']))
        conn.commit()
        cur.close()

# host = '10.10.10.148'
# port = '5432'
# user = 'postgres'
# password = 'tech5d_ndww'
# dbname = 'geodatabase'
# conn = psycopg2.connect('host={} port={} user={} password={} dbname={}'.format(host,port,user,password,dbname))
# cur = conn.cursor()
#
# tablename = 'chuanzha_lyg'
# strsql = 'select gid,' \
#          'geom,jzlx from {} where name=\'鲁河闸\''.format(tablename)
# cur.execute(strsql)
# results = cur.fetchall()
# cols = [i.name for i in cur.description]
# cur.close()


