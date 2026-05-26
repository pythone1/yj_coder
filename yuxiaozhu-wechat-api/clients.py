import os
from datetime import datetime

from ollama import Client
from openai import OpenAI

from water_color import *
from qweather import *
from waterqa import *

class ollmAgent():
    def __init__(self,session_id,model='qwen3:8b'):        
        self.model = model
        self.client = Client(host  ='http://localhost:11434')   

        self.messages = []      

        self.session_id = session_id
        self.session_history_path = r'D:\pymethods\local_knowledge_LLM\sessions'
          

    def load_session_history(self,weather_data,waterqa_data):
        ''' 
        加载历史对话
        '''
        # session_file = os.path.join(self.session_history_path,f"{self.session_id}.json")
        # if os.path.exists(session_file):
        #     with open(session_file,'r',encoding='utf-8') as f:
        #         self.messages = json.load(f)
        self.messages.append({
            'role':'system',
            'content':f"""你是一位螃蟹养殖技术专家，请根据上下文及未来七天天气状况和当前水质情况回答用户问题。\
                未来7天天气状况：{weather_data}。
                当天水质情况：{waterqa_data}。
                今天日期：{datetime.now().strftime("%Y年%m月%d日")} /think"""               
        }) 

    def save_session_history(self):
        ''' 保存历史对话 '''
        session_file = os.path.join(self.session_history_path,f"{self.session_id}.json")
        with open(session_file,'w',encoding='utf-8') as f:
            json.dump(self.messages,f,ensure_ascii=False,indent=2)

    def call_function_safely(self,response):
        tool_call = response.message.tool_calls[0]
        function_name = tool_call.function.name
        arguments = tool_call.function.arguments

        function_to_call = self.function_map.get(function_name)

        if function_to_call:
            try:
                result = function_to_call(**arguments)
                return result
            except Exception as e:
                print(f"工具调用失败：{e}")
        else:
            print(f"{function_name} is not a recognized function")

class openaiAgent():
    def __init__(self,session_id,model='glm-4.5v',clien_name='zhipu'):
        cltinfo = {
            'zhipu':{
                'api_key':'37396eda5f13401ca14d9570f52b0046.Lbsee8coUifF4b6K',
                'base_url': 'https://open.bigmodel.cn/api/paas/v4/'
            }            
        }

        self.client = OpenAI(api_key=cltinfo[clien_name]['api_key'],base_url=cltinfo[clien_name]['base_url'])
        self.model = model

        self.messages = []

        self.session_id = session_id
        self.session_history_path = r'D:\pymethods\local_knowledge_LLM\sessions'

        self.function_map = {
            'water_color_main':water_color_main,
        }

        self.tools = [{
            'type':'function',
            'function':{
                'name': "water_color_main",
                'description': '识别给定图片的水体颜色',
                'parameters':{
                    'type':'object',
                    'properties':{
                        'imgfiles':{'type':'string','description':'图片地址，如果有多张图片用","隔开'}
                    },
                    'required':['imgfiles']                
                }            
            }
        }]

    def load_session_history(self):
        ''' 
        加载历史对话
        '''
        session_file = os.path.join(self.session_history_path,f"{self.session_id}.json")
        if os.path.exists(session_file):
            with open(session_file,'r',encoding='utf-8') as f:
                self.messages = json.load(f)
        else:
            # self.messages.append({
            #     'role':'system',
            #     'content':f"""你是一个专业的大闸蟹病害诊断助手。你的任务是根据用户上传的图片和描述，诊断大闸蟹可能患有的病害，回答描述时语句尽量连贯，包括分析过程及描述的病害可能存在的阶段性，并提供相应的防治建议；回答时请仔细理解每一次输入的文本和图片，每个描述都很重要，描述有变化需要及时修正你的回答。
            #         严格限制：
            #         1.只回答与大闸蟹病害相关的问题
            #         2.对于任何与大闸蟹病害无关的问题，请礼貌拒绝回答，拒绝回答时，请回复："抱歉，我只能回答大闸蟹病害相关问题，请咨询其他领域专家"
            #         你的专业知识包括:
            #         1.大闸蟹常见病害（如黑鳃病、甲壳溃疡病、烂肢病、水肿病、肠炎病、弧菌病、弗氏柠檬酸杆菌感染症、固着类纤毛虫病、蟹奴病（臭虫蟹病）、颤抖病（支原体病）、微孢子虫病、水霉病、肝胰腺疾病、蜕壳不遂病、青泥苔病等）
            #         2.病害症状识别
            #         3.病害成因分析
            #         4.防治方法和用药建议
            #         5.养殖环境管理建议
            #         需要注意区分：
            #         1、水霉病和纤毛虫病容易错，都有附着物，水霉病是白颜色，纤毛虫病是黄绿色
            #         2、烂肢病和弧菌病容易错，烂肢病患病河蟹腹部和附肢容易发生腐烂，腹部出现灰黄或灰黑色斑点，肛门红肿，行动迟缓，出现摄食能力下降甚至不进食现象，蜕壳困难最终导致死亡。弧菌病腹部和附肢腐烂，食欲下降，身体颜色变浅，发育蜕壳迟缓，喜欢匍匐于岸边直至死亡，死亡和濒临死亡的病蟹体内有大量凝血块
            #         3、肝胰腺疾病的特点主要体现在肝胰腺腐烂坏死，得病导致甲壳上附着大量有机碎屑、藻类、原生动物等，注意和纤毛虫病区分它不会附着大量有机碎屑、藻类、原生动物等
            #         """               
            # })
            self.messages.append({
                'role':'system',
                'content':f"""你是一个专业的大闸蟹养殖技术专家与病害诊断助手。你的任务是根据用户上传的图片和描述，分析大闸蟹养殖中遇到的水色、水草状态问题诊断大闸蟹可能患有的病害，回答描述时语句尽量连贯，包括分析过程及病害可能存在的阶段性，并提供相应的防治建议；回答时请仔细理解每一次输入的文本和图片，每个描述都很重要，描述有变化需要及时修正你的回答。
                    严格限制：
                    1.只回答与大闸蟹养殖技术以及病害相关的问题
                    2.对于任何与大闸蟹养殖技术以及病害无关的问题，请礼貌拒绝回答，拒绝回答时，请回复："抱歉，我只能回答大闸蟹养殖技术及病害相关问题，请咨询其他领域专家"
                    你的专业知识包括:
                    1.大闸蟹常见病害（如黑鳃病、甲壳溃疡病、烂肢病、水肿病、肠炎病、弧菌病、弗氏柠檬酸杆菌感染症、固着类纤毛虫病、蟹奴病（臭虫蟹病）、颤抖病（支原体病）、微孢子虫病、水霉病、肝胰腺疾病、蜕壳不遂病、青泥苔病等）
                    2.病害症状识别
                    3.病害成因分析
                    4.防治方法和用药建议
                    5.养殖环境管理建议
                    6.大闸蟹常见水色（如蓝绿色、灰绿、淡绿、翠绿、黄绿、浓绿、红褐色、酱油色、黑色、黄色）
                    7.不同水色对应的藻相、养殖评价与应对措施
                    8.水草健康状况（如水草挂脏、上浮、死亡）
                    需要注意区分：
                    1、水霉病和纤毛虫病容易错，都有附着物，水霉病是白颜色，纤毛虫病是黄绿色
                    2、烂肢病和弧菌病容易错，烂肢病患病河蟹腹部和附肢容易发生腐烂，腹部出现灰黄或灰黑色斑点，肛门红肿，行动迟缓，出现摄食能力下降甚至不进食现象，蜕壳困难最终导致死亡。弧菌病腹部和附肢腐烂，食欲下降，身体颜色变浅，发育蜕壳迟缓，喜欢匍匐于岸边直至死亡，死亡和濒临死亡的病蟹体内有大量凝血块
                    3、肝胰腺疾病的特点主要体现在肝胰腺腐烂坏死，得病导致甲壳上附着大量有机碎屑、藻类、原生动物等，注意和纤毛虫病区分它不会附着大量有机碎屑、藻类、原生动物等
                    """               
            })

    def save_session_history(self):
        ''' 保存历史对话 '''
        session_file = os.path.join(self.session_history_path,f"{self.session_id}.json")
        with open(session_file,'w',encoding='utf-8') as f:
            json.dump(self.messages,f,ensure_ascii=False,indent=2)
    
    def call_function_safely(self,response):
        tool_call = response.choices[0].message.tool_calls[0]
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        function_to_call = self.function_map.get(function_name)

        if function_to_call:
            try:
                result = function_to_call(**arguments)
                return result
            except Exception as e:
                print(f"工具调用失败：{e}")
        else:
            print(f"{function_name} is not a recognized function")

