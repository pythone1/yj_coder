import requests
import base64
import json
import re

import cv2
import numpy as np
from openai import OpenAI

def water_color(imgfile):
    '''
    水色
    '''
    if imgfile.startswith('http'):
        response = requests.get(imgfile)
        img = cv2.imdecode(np.frombuffer(response.content,np.uint8),cv2.IMREAD_COLOR)
    else:
        img = cv2.imread(imgfile)
    hsv = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
    h,v = hsv[:,:,0].flatten(),hsv[:,:,2].flatten()/255
    
    h_x = [0,25,30,60,90,180]
    h_ratio = [len(h[(h>h_x[i]) & (h<h_x[i+1])]) / len(h) for i in range(len(h_x)-1)]
    
    v_x = [0,0.4,0.6,0.8,1]
    v_ratio = [len(v[(v>v_x[i]) & (v<v_x[i+1])]) / len(v) for i in range(len(v_x)-1)]

    if v_ratio[0] > 0.4:
        # 低明度占比大
        if h_ratio[2] > 0.5:
            # 绿色
            return '浓绿色'
        else:
            return '黑色'
    else:
        # 高明度占比大
        if max(h_ratio) == h_ratio[3]:
            return '蓝绿色'
        elif max(h_ratio) == h_ratio[2]:
            return '黄绿色'
        elif max(h_ratio) == h_ratio[1]:
            if v_ratio[1] > v_ratio[2]:
                # 相对低明度，硅藻水，归入绿色
                return '黄绿色'
            else:
                # 相对高明度，黄色贫水，高明度
                return '黄色'
        elif max(h_ratio) == h_ratio[0]:
            return '红褐色'
        else:
            return '其他'
        
def encode_image(image_path):
    '''
    图像编码
    '''
    if image_path.startswith('http'):
        response = requests.get(image_path)
        return base64.b64encode(response.content).decode('utf-8')
    else:
        with open(image_path,'rb') as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
        
def extract_numbers(text):
    '''
    提取数字
    '''
    numbers = re.findall(r'\d+',text)
    return numbers
        
def water_coverage(imgfile):
    '''
    利用ai分析水域面积占比
    '''
    client = OpenAI(api_key='34f49fd8060f4994ad07940a1177fa02.thiYG0ONxQ4FHL8f',
                    base_url='https://open.bigmodel.cn/api/paas/v4/')
    messages = [{
        'role':'user',
        'content':[{
            'type':'text',
            'text':'分析图片中水面面积占比，json格式返回百分比数值，不要添加额外内容'
        },{
            'type':'image_url',
            'image_url':{'url':f"data:image/jpeg;base64,{encode_image(imgfile)}"}
        }]
    }]

    response = client.chat.completions.create(
        model='glm-4.5v',
        messages=messages
    )

    print(response)
    message_content = response.choices[0].message.content

    num = int(extract_numbers(message_content)[0])

    return num
        
def water_color_main(imgfiles):
    '''
    识别图片中水体颜色
    '''
    imgfiles = imgfiles.split(',')

    if len(imgfiles)==1:
        if water_coverage(imgfiles[0])>=90:
            return f"图片中水体为{water_color(imgfiles[0])}"
        else:
            return ""

    if len(imgfiles)>1:
        results = []
        for i,f in enumerate(imgfiles):
            if water_coverage(f)>=90:
                results.append(f"第{i+1}张图片：{water_color(f)}")
        if len(results)>0:
            return ';'.join(results)
        else:
            return ""
