import pymysql
from dbutils.pooled_db import PooledDB
from utils.config_loader import CONFIGS


class MySQLPool:
    config = {
        "creator": pymysql,
        "host": CONFIGS["mysql"]["host"],
        "port": int(CONFIGS["mysql"]["port"]),
        "user": CONFIGS["mysql"]["user"],
        "password": CONFIGS["mysql"]["password"],
        "db": CONFIGS["mysql"]["db"],
        "charset": "utf8",
        # 连接池最大连接数量
        "maxconnections": 70,
        "cursorclass": pymysql.cursors.DictCursor,
    }
    pool = PooledDB(**config)

    def __enter__(self):
        self.conn = MySQLPool.pool.connection()
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, type, value, trace):
        self.cursor.close()
        self.conn.close()


# 装饰器
def DB_CONN(func):
    def wrapper(*args, **kw):
        with MySQLPool() as db:
            result = func(db, *args, **kw)
        return result

    return wrapper


# example
# @DB_CONN
# def proc(db, *args, **kw):
#     try:
#         db.cursor.execute("SQL")
#         db.conn.commit()
#         return 0
#     except Exception as e:
#         db.conn.rollback()
#         return 1
