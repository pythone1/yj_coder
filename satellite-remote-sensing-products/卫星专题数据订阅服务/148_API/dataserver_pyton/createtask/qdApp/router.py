import os
from django.http import HttpResponse
import json
import _thread
import time
from utils.mysql_pool import DB_CONN
import xlrd
from .logger import cusLogger

log = cusLogger("excel_process").getLogger()


def checkFileValid(file):
    if not os.path.exists(file):
        raise Exception("文件不存在")

    try:
        # 打开 excel 表格
        book = xlrd.open_workbook(file)
    except xlrd.XLRDError as e:
        raise e;

    return book;


def index(request):
    return HttpResponse("hello world")

# 解析手工断面
def dmManualProcess(excel_file, pos):
    # 打开excel文件
    book = xlrd.open_workbook(excel_file)
    sh = book.sheet_by_index(0);

    # 行数
    rows_cnt = sh.nrows;
    # 列数
    cols_cnt = sh.ncols;

    # 遍历每一行
    Keys = ["area", "river_name", "section_name", "section_no", "month", "category", "temp", "ph", "doval", "codmn",
            "bod", "nh4", "oil", "vpc", "gong", "qian", "cod", "tp", "tong", "xin", "fluoride", "xi", "shen", "ge",
            "cr6", "cyanide", "anionic_surfactant", "sulfide", "level"]

    # 如果列数不正确，那么放弃解析
    if (len(Keys) > cols_cnt):
        return

    for i in range(1, rows_cnt):
        Values = [];
        for j in range(0, cols_cnt):

            # 4列和5列是年和月，需要拼接起来
            if j == 5:
                continue
            if j == 4:
                month = sh.row_values(i)[4] + '-' + sh.row_values(i)[5];
                cur_month = time.strftime('%Y-%m', time.localtime(time.time()))
                # 判断下时间，将大于当前月份的数据跳过
                if month > cur_month:
                    break;
                Values.append(month);
            else:
                Values.append(sh.row_values(i)[j]);

            if len(Values) == len(Keys):
                break;

        if len(Values) == len(Keys):
            log.info(Keys);
            log.info(Values);
            db_insert_dm_record(Keys, Values)


def parseDmManual(excel_file, book):
    # 检查excel文件里的是否存在相关字段

    log.info("-----parseDmManual--------")
    log.info("当前excel文件工作表数量为 {0}".format(book.nsheets))
    log.info("Sheet名字为: {0}".format(book.sheet_names()))

    # 打开第一个sheet
    sh = book.sheet_by_index(0);
    log.info("{0}行,{1}列".format(sh.nrows, sh.ncols))
    if (sh.nrows == 0) or (sh.ncols == 0):
        raise Exception("未在文件中找到断面数据")

    if (sh.row_values(0)[2] != '断面名称') \
            or (sh.row_values(0)[3] != '断面编码') \
            or (sh.row_values(0)[4] != '年') \
            or (sh.row_values(0)[5] != '月'):
        raise Exception("文件中数据列格式不正确")

    try:
        _thread.start_new_thread(
            dmManualProcess, (excel_file, 1)
        )
    except Exception as e:
        return HttpResponse(json.dumps(httpResult(500, str(e))))


# 解析excel文件
def ParseImportExcel(request):
    if request.method == "GET":
        return HttpResponse(json.dumps(httpResult(400, "不支持GET方法")))
    excel_file = request.POST.get("excel_file")
    # excel_file = "/Users/sr/study/code/projects/qd/logs/0524.xlsx"

    excel_type = request.POST.get('excel_type')
    # print(excel_type)
    if excel_file == None:
        return HttpResponse(json.dumps(httpResult(201, "缺少文件路径参数")))

    if excel_type == None:
        return HttpResponse(json.dumps(httpResult(201, "缺少解析类型参数")))

    excelBook = None
    # 检查文件合法性
    try:
        # 获取 excel 读取对象
        excelBook = checkFileValid(excel_file)
    except Exception as e:
        return HttpResponse(json.dumps(httpResult(400, str(e))))

    try:

        if excel_type == 'dm_manual':
            parseDmManual(excel_file, excelBook)
        # elif excel_type == 'soil':
        #     print(11)
    except Exception as e:
        return HttpResponse(json.dumps(httpResult(400, str(e))))

    return HttpResponse(json.dumps(httpResult(200, "解析成功")))


def httpResult(code, msg):
    res = {"code": 200, "msg": "success"}
    res["code"] = code
    res["msg"] = msg
    return res


@DB_CONN
def db_insert_dm_record(db, Keys, Values):
    try:

        # 查询是否有相同的记录，如果已有，则不插入
        sql = "SELECT * FROM qdenv2_section_data_manual where section_name = '{0}' and month = '{1}'".format(Values[2],
                                                                                                             Values[4])
        db.cursor.execute(sql)
        res = db.cursor.fetchall();

        if res != None and len(res) > 0:
            return;

        # 插入数据，拼接SQL
        sql = "INSERT INTO qdenv2_section_data_manual ("
        for i in range(0, len(Keys)):
            sql += Keys[i];
            if (i != len(Keys) - 1):
                sql += ','

        sql += ') VALUES ('

        for i in range(0, len(Values)):
            if Values[i] == None or Values[i] == '':
                sql += "null"
            else:
                sql += "'{0}'".format(Values[i])
            if (i != len(Values) - 1):
                sql += ','

        sql += ')'

        db.cursor.execute(sql)
        db.conn.commit()
        return 0
    except Exception as e:
        print(str(e))
        db.conn.rollback()
        return 1
