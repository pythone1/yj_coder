import glob
import json
import datetime
import os
from django.http import HttpResponse

from .initParameters import *
from .sendEmail import *

def test(request):
    a = request.GET.get("a")
    b = request.GET.get("b")
    c = a + b
    return HttpResponse(json.dumps(httpResult(200, c), ensure_ascii=False))

def watersVectorizationTask(request):
    '''
    接收提取水系矢量的任务，解析参数、发布任务、返回任务发布情况
    :param request: HttpRequest对象
    :return: json格式字符串
    '''
    # 处理post请求
    if request.method == "POST":
        return HttpResponse(json.dumps(httpResult(400, "不支持POST方法"), ensure_ascii=False))

    # 参数解析
    try:
        config = getWtVctParams(request)
    except:
        return HttpResponse(json.dumps(httpResult(400, "参数错误"), ensure_ascii=False))

    try:
        task_name = '提取水系矢量'
        generateTask(task_name, config)
    except:
        return HttpResponse(json.dumps(httpResult(400, "任务生成失败"), ensure_ascii=False))

    return HttpResponse(json.dumps(httpResult(200, "任务已接收"), ensure_ascii=False))

def idtWatersOnStlImageTask(request):
    '''
    接收基于卫星影像识别水域的任务，解析参数、发布任务、返回任务发布情况
    :param request: HttpRequest对象
    :return: json格式字符串
    '''
    # 处理post请求
    if request.method == "POST":
        return HttpResponse(json.dumps(httpResult(400, "不支持POST方法"), ensure_ascii=False))

    # 参数解析
    try:
        config = getIdtWatersOnStlImageParams(request)

    except:
        return HttpResponse(json.dumps(httpResult(400, "参数错误"), ensure_ascii=False))

    # 生成任务
    try:
        task_name = '基于卫星影像识别水域'
        generateTask(task_name, config)
    except:
        return HttpResponse(json.dumps(httpResult(400, "任务生成失败"), ensure_ascii=False))

    return HttpResponse(json.dumps(httpResult(200, "任务已接收"), ensure_ascii=False))

def idtWatersOnAerImageTask(request):
    '''
    接收基于卫星影像识别水域的任务，解析参数、发布任务、返回任务发布情况
    :param request: HttpRequest对象
    :return: json格式字符串
    '''
    # 处理post请求
    if request.method == "POST":
        return HttpResponse(json.dumps(httpResult(400, "不支持POST方法"), ensure_ascii=False))

    # 参数解析
    try:
        config = getIdtWatersOnAerImageParams(request)
    except:
        return HttpResponse(json.dumps(httpResult(400, "参数错误"), ensure_ascii=False))

    # 生成任务
    try:
        task_name = '基于航空影像识别水域'
        generateTask(task_name, config)
    except:
        return HttpResponse(json.dumps(httpResult(400, "任务生成失败"), ensure_ascii=False))

    return HttpResponse(json.dumps(httpResult(200, "任务已接收"), ensure_ascii=False))

def waterqaSpecOnlyTask(request):
    '''
    接收纯依靠光谱的水色指标计算任务，解析参数、发布任务、返回任务发布情况
    :param request: HttpRequest对象
    :return: json格式字符串
    '''
    # 处理post请求
    if request.method == "POST":
        return HttpResponse(json.dumps(httpResult(400, "不支持POST方法"), ensure_ascii=False))

    # 参数解析
    try:
        config = getWaterqaSpecOnlyParams(request)
    except:
        return HttpResponse(json.dumps(httpResult(400, "参数错误"), ensure_ascii=False))

    # 生成任务
    try:
        task_name = '水色分布'
        generateTask(task_name, config)
    except:
        return HttpResponse(json.dumps(httpResult(400, "任务生成失败"), ensure_ascii=False))

    return HttpResponse(json.dumps(httpResult(200, "任务已接收"), ensure_ascii=False))

def waterqaRetrivalTask(request):
    '''
    接收水质指标反演任务，解析参数、发布任务、返回任务发布情况
    :param request: HttpRequest对象
    :return: json格式字符串
    '''
    # 处理post请求
    if request.method == "POST":
        return HttpResponse(json.dumps(httpResult(400, "不支持POST方法"), ensure_ascii=False))

    # 参数解析
    try:
        config = getWaterqaRetrivalParams(request)
    except:
        return HttpResponse(json.dumps(httpResult(400, "参数错误"), ensure_ascii=False))

    # 生成任务
    try:
        task_name = '水质参数反演'
        generateTask(task_name, config)
    except:
        return HttpResponse(json.dumps(httpResult(400, "任务生成失败"), ensure_ascii=False))

    return HttpResponse(json.dumps(httpResult(200, "任务已接收"), ensure_ascii=False))

def farmlandVectorizationTask(request):
    '''
    接收绘制农田范围的任务，解析参数、发布任务、返回任务发布情况
    :param request: HttpRequest对象
    :return: json格式字符串
    '''
    # 处理post请求
    if request.method == "POST":
        return HttpResponse(json.dumps(httpResult(400, "不支持POST方法"), ensure_ascii=False))

    # 参数解析
    try:
        config = getFmVctParams(request)
    except:
        return HttpResponse(json.dumps(httpResult(400, "参数错误"), ensure_ascii=False))

    # 生成任务
    try:
        task_name = '绘制农田范围'
        generateTask(task_name, config)
    except:
        return HttpResponse(json.dumps(httpResult(400, "任务生成失败"), ensure_ascii=False))

    return HttpResponse(json.dumps(httpResult(200, "任务已接收"), ensure_ascii=False))

def landcoverVectorizationTask(request):
    '''
    接收绘制农田范围的任务，解析参数、发布任务、返回任务发布情况
    :param request: HttpRequest对象
    :return: json格式字符串
    '''
    # 处理post请求
    if request.method == "POST":
        return HttpResponse(json.dumps(httpResult(400, "不支持POST方法"), ensure_ascii=False))

    # 参数解析
    try:
        config = getLcVctParams(request)
    except:
        return HttpResponse(json.dumps(httpResult(400, "参数错误"), ensure_ascii=False))

    # 生成任务
    try:
        task_name = '土地覆被分类'
        generateTask(task_name, config)
    except:
        return HttpResponse(json.dumps(httpResult(400, "任务生成失败"), ensure_ascii=False))

    return HttpResponse(json.dumps(httpResult(200, "任务已接收"), ensure_ascii=False))

def s1UpdateTask(request):
    '''
    接收哨兵一号影像更新的任务，解析参数、发布任务、返回任务发布情况
    :param request: HttpRequest对象
    :return: json格式字符串
    '''
    # 处理post请求
    if request.method == "POST":
        return HttpResponse(json.dumps(httpResult(400, "不支持POST方法"), ensure_ascii=False))

    # 参数解析
    try:
        config = getS1UpdataParams(request)
    except:
        return HttpResponse(json.dumps(httpResult(400, "参数错误"), ensure_ascii=False))

    # 生成任务
    try:
        task_name = '哨兵一号影像更新'
        generateTask(task_name, config)
    except:
        return HttpResponse(json.dumps(httpResult(400, "任务生成失败"), ensure_ascii=False))

    return HttpResponse(json.dumps(httpResult(200, "任务已接收"), ensure_ascii=False))

def s2UpdateTask(request):
    '''
    接收哨兵二号影像更新的任务，解析参数、发布任务、返回任务发布情况
    :param request: HttpRequest对象
    :return: json格式字符串
    '''
    # 处理post请求
    if request.method == "POST":
        return HttpResponse(json.dumps(httpResult(400, "不支持POST方法"), ensure_ascii=False))

    # 参数解析
    try:
        config = getS2UpdataParams(request)
    except:
        return HttpResponse(json.dumps(httpResult(400, "参数错误"), ensure_ascii=False))

    # 生成任务
    try:
        task_name = '哨兵二号影像更新'
        generateTask(task_name, config)
    except:
        return HttpResponse(json.dumps(httpResult(400, "任务生成失败"), ensure_ascii=False))

    return HttpResponse(json.dumps(httpResult(200, "任务已接收"), ensure_ascii=False))

def s3UpdateTask(request):
    '''
    接收哨兵三号影像更新的任务，解析参数、发布任务、返回任务发布情况
    :param request: HttpRequest对象
    :return: json格式字符串
    '''
    # 处理post请求
    if request.method == "POST":
        return HttpResponse(json.dumps(httpResult(400, "不支持POST方法"), ensure_ascii=False))

    # 参数解析
    try:
        config = getS3UpdataParams(request)
    except:
        return HttpResponse(json.dumps(httpResult(400, "参数错误"), ensure_ascii=False))

    # 生成任务
    try:
        task_name = '哨兵三号影像更新'
        generateTask(task_name, config)
    except:
        return HttpResponse(json.dumps(httpResult(400, "任务生成失败"), ensure_ascii=False))

    return HttpResponse(json.dumps(httpResult(200, "任务已接收"), ensure_ascii=False))

def ccrsImgUpdateTask(request):
    '''
    接收中国资源卫星应用影像获取的任务，解析参数、发布任务、返回任务发布情况
    :param request: HttpRequest对象
    :return: json格式字符串
    '''
    # 处理post请求
    if request.method == "POST":
        return HttpResponse(json.dumps(httpResult(400, "不支持POST方法"), ensure_ascii=False))

    # 参数解析
    try:
        config = getCCRSImgUpdataParams(request)
    except:
        return HttpResponse(json.dumps(httpResult(400, "参数错误"), ensure_ascii=False))

    # 生成任务
    try:
        task_name = '中国资源卫星应用影像获取'
        generateTask(task_name, config)
    except:
        return HttpResponse(json.dumps(httpResult(400, "任务生成失败"), ensure_ascii=False))

    return HttpResponse(json.dumps(httpResult(200, "任务已接收"), ensure_ascii=False))

def aerialImgUpdateTask(request):
    '''
    接收哨兵三号影像更新的任务，解析参数、发布任务、返回任务发布情况
    :param request: HttpRequest对象
    :return: json格式字符串
    '''
    # 处理post请求
    if request.method == "POST":
        return HttpResponse(json.dumps(httpResult(400, "不支持POST方法"), ensure_ascii=False))
    # 参数解析
    try:
        config = getAerialImgUpdataParams(request)
    except:
        return HttpResponse(json.dumps(httpResult(400, "参数错误"), ensure_ascii=False))

    # 生成任务
    try:
        task_name = '无人机影像更新'
        generateTask(task_name, config)
    except:
        return HttpResponse(json.dumps(httpResult(400, "任务生成失败"), ensure_ascii=False))

    return HttpResponse(json.dumps(httpResult(200, "任务已接收"), ensure_ascii=False))

def gaodePOITask(request):
    '''
    接收高德POI数据获取的任务，解析参数、发布任务、返回任务发布情况
    :param request: HttpRequest对象
    :return: json格式字符串
    '''
    # 处理post请求
    if request.method == "POST":
        return HttpResponse(json.dumps(httpResult(400, "不支持POST方法"), ensure_ascii=False))

    # 参数解析
    try:
        config = getGaodePOIParams(request)
    except:
        return HttpResponse(json.dumps(httpResult(400, "参数错误"), ensure_ascii=False))

    # 生成任务
    try:
        task_name = '高德POI数据获取'
        generateTask(task_name, config)
    except:
        return HttpResponse(json.dumps(httpResult(400, "任务生成失败"), ensure_ascii=False))

    return HttpResponse(json.dumps(httpResult(200, "任务已接收"), ensure_ascii=False))

def getPrecipitationTask(request):
    '''
    接收降雨量数据查询的任务，解析参数、发布任务、返回任务发布情况
    :param request: HttpRequest对象
    :return: json格式字符串
    '''
    # 处理post请求
    if request.method == "POST":
        return HttpResponse(json.dumps(httpResult(400, "不支持POST方法"), ensure_ascii=False))

    # 参数解析
    try:
        config = getPrecipitationParams(request)
    except:
        return HttpResponse(json.dumps(httpResult(400, "参数错误"), ensure_ascii=False))

    # 生成任务
    try:
        task_name = '降雨量数据查询'
        generateTask(task_name, config)
    except:
        return HttpResponse(json.dumps(httpResult(400, "任务生成失败"), ensure_ascii=False))

    return HttpResponse(json.dumps(httpResult(200, "任务已接收"), ensure_ascii=False))

def generateTask(task_name,config):
    '''
    生成任务
    :param task_name: str 任务名称
    :param config: dict 任务执行参数
    :return:
    '''
    # 编辑任务内容
    taskinfo = dict()
    taskinfo['任务编号'] = config['user']['task_id']
    taskinfo['项目名称'] = config['user']['prj_name']
    taskinfo['执行参数'] = "见附件"
    # 任务名称
    subject = task_name

    # 任务内容
    body = ''
    for k, v in taskinfo.items():
        body = body + '{}: {}<br>'.format(k, v)

    attachment = []
    # 附件-矢量范围
    try:
        roi_zipfile = config['user']['roi_file'][0:-4] + '.zip'
        if os.path.exists(roi_zipfile):
            pass
        else:
            roi_files = glob.glob(config['user']['roi_file'][0:-4] + '*')
            compressFiles(roi_files, roi_zipfile)
            attachment.append(roi_zipfile)
    except:
        pass

    # 附件-执行参数
    config_file = os.path.join(config['savepath']['taskconfigs'], config['user']['task_id'] + '.json')
    with open(config_file, 'w') as f:
        json.dump(config, f, ensure_ascii=False)
    attachment.append(config_file)

    # 发布
    smtp_server = login_gmail_smtp(config['gmail']['sender'], config['gmail']['password'])

    send_email(smtp_server, config['gmail']['sender'], config['gmail']['recipients'], subject, body, attachment)

def httpResult(code,msg):
    '''
    格式化返回内容
    :param code:
    :param msg:
    :param service_url:
    :return:
    '''
    res = dict()
    res["code"] = code
    res["message"] = msg

    return res