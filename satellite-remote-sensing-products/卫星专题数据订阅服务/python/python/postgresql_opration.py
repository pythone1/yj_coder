import psycopg2

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

    conn = psycopg2.connect('host={} port={} user={} password={} dbname={}'.format(host,port,user,password))
    cur = conn.cursor()
    cur.execute(strsql)
    results = cur.fetchall()

    return results

# conn = psycopg2.connect('host=10.10.10.148 port=5432 user=postgres password=tech5d_ndww dbname=geodatabase')
# cur = conn.cursor()
# srctable = 'chuanzha_lyg'
# srcimg_url = "\'云善河套闸\'"
# strsql = "SELECT jzlx,gid FROM {} WHERE name={}".format(srctable,srcimg_url)
# cur.execute(strsql)
# rows = cur.fetchall()
# for row in rows:
#     print(row)

files = ['卫星_传感器_产品级别_拍摄开始时间_拍摄结束时间_产品制备时间_中心经纬度','卫星_传感器_产品级别_拍摄开始时间_拍摄结束时间_产品制备时间_中心经纬度']
a = ['_'.join(f.split('_')[0:3]+f.split('_')[3].split('T')) for f in files]
print(a)