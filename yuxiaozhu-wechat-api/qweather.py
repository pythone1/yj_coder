import requests
import json
import traceback

base_url = 'https://api.qweather.net'
api_key = '6ae458e5a8ce4986bbfc71e0dad17fa4'

# base_url = 'https://j767ca2f84.re.qweatherapi.com'
# api_key = '254654e783404dc282cc942f67e4ed29'

def get_locationID(city_name):
    ''' 获取城市编码 '''
    q_url = base_url + '/geo/v2/city/lookup'

    params = {
        'location':city_name,
        'key':api_key,
        'lang':'zh'
    }

    try:
        response = requests.get(q_url,params=params)
        response.raise_for_status() # 检查请求是否成功，失败时抛出异常
        results = response.json()
        return results['location'][0]['id']
    
    except Exception as e:
        return {'status':'error',
                'message':str(e),
                'traceback': traceback.format_exc(),
                'code':500}

def get_weather_now(location):
    ''' 
    查询实时天气 
    location: str 城市名或经纬度(116.41,39.92)
    '''
    q_url = base_url + '/v7/weather/now'

    # 如果location是城市名转为城市编码
    if ',' not in location:
        location = get_locationID(location)

    params = {
        'location':location,
        'key':api_key,
        'lang':'zh',
        'unit':'m' # 公制单位，公里、摄氏度
    }

    try:
        response = requests.get(q_url,params=params)
        response.raise_for_status() # 检查请求是否成功，失败时抛出异常
        results = response.json()
        return results['now']        
    
    except Exception as e:
        return {'status':'error',
                'message':str(e),
                'traceback': traceback.format_exc(),
                'code':500}

def get_weather_daypred(location='101190103',days=3):
    ''' 
    查询未来几天的天气
    location: str 城市名或经纬度
    days: int 可选[3,7,10,15,30]  
    '''
    q_url = base_url + f'/v7/weather/{days}d'

    # # 如果location是城市名转为城市编码
    # if ',' not in location:
    #     location = get_locationID(location)
    print(location)

    params = {
        'location':location,
        'key':api_key,
        'lang':'zh',
        'unit':'m' # 公制单位，公里、摄氏度
    }

    try:
        print(q_url)
        response = requests.get(q_url,params=params)
        print(response)
        response.raise_for_status() # 检查请求是否成功，失败时抛出异常
        results = response.json()
        print(results)
        return results['daily']        
    
    except Exception as e:
        return {'status':'error',
                'message':str(e),
                'traceback': traceback.format_exc(),
                'code':500}
    
def get_weather_daypred_from_sql(days=7):
    ''' 从数据库获取天气数据 '''
    url = f'http://118.190.136.20:8087/prod-api/system/dfmsWeatherData/list_anno_day?pageSize={days}'

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