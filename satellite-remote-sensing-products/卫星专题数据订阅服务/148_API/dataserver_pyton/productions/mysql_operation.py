import mysql.connector
import json

def insertItems2mysql(df,tablename,config):
    '''
    向mysql中的数据表插入记录
    :param df: pd.DataFrame 待插入内容
    :param tablename: str 表名
    :param config: dict 包含mysql连接参数
    :return:
    '''

    host = config['host']
    database = config['database']
    user = config['user']
    port = config['port']
    password = config['password']
    conn = mysql.connector.connect(host=host, port=port, user=user, password=password, db=database)
    cur = conn.cursor()

    # insert items
    for i in range(df.shape[0]):
        ##查询数据库中是否已有相同的数据
        select_statement = "SELECT * FROM {0} WHERE project='{1}' and regional='{2}' and record_time='{3}'"\
            .format(tablename,df.loc[i, 'prj_name'], df.loc[i, 'geometry'], df.loc[i, 'record_time'])
        cur.execute(select_statement)

        if cur.fetchone():
            pass
        else:
            #插入查询信息
            insert_statement = "INSERT INTO {0} (project,regional,record_time,result_value) VALUES (%s,%s,%s,%s)".format(tablename)
            cur.execute(insert_statement, (df.loc[i, 'prj_name'], df.loc[i, 'geometry'], df.loc[i, 'record_time'],json.dumps(df.loc[i, 'precipitation_point'])))

            conn.commit()
    cur.close()


