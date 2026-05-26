import requests
import json
import traceback

import pandas as pd

def get_waterqa_now():
    ''' 获取当前水质数据 '''
    url = 'http://118.190.136.20:8087/prod-api/system/dfmsWaterData/list_anno?tbid=tb01&pageSize=1'

    try:
        response = requests.get(url)
        response.raise_for_status() # 检查请求是否成功，失败时抛出异常
        results = response.json()
        return results
    
    except Exception as e:
        return {'status':'error',
                'message':str(e),
                'traceback': traceback.format_exc(),
                'code':500}
