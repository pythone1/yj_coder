import os
import traceback
import json
from datetime import datetime

from ollama import Client

from flask import Flask, request, Response
from openai import OpenAI
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.document_loaders import DirectoryLoader,Docx2txtLoader
import pandas as pd

from qweather import *
from waterqa import *

class ollmAgent():
    def __init__(self,session_id):
        self.model = 'qwen3:8b'
        self.client = Client(host='http://localhost:11434')

        self.session_history_path = r'D:\pymethods\local_knowledge_LLM\sessions'

        self.session_id = session_id
        self.messages = []     
    
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
                今天日期：{datetime.now().strftime("%Y年%m月%d日")}"""               
        })
    
    def save_session_history(self):
        ''' 保存历史对话 '''
        session_file = os.path.join(self.session_history_path,f"{self.session_id}.json")
        with open(session_file,'w',encoding='utf-8') as f:
            json.dump(self.messages,f,ensure_ascii=False,indent=2)

def load_db(db_faiss_path):
    ''' 加载数据库 '''
    embeddings = HuggingFaceEmbeddings(model_name = 'sentence-transformers/all-mpnet-base-v2')
    db = FAISS.load_local(db_faiss_path,embeddings,allow_dangerous_deserialization=True)

    return db.as_retriever(search_kwargs={'k':10})    

def quary_on_local_knowdge_with_ollama(session_id,user_input):
    ''' 
    基于ollama的本地知识问答
    session_id：str 任务id,用于记录、查询历史对话内容。唯一
    user_input: str 用户提问
    '''
    try:
        # 天气
        weather_data = pd.DataFrame(get_weather_daypred(location='高淳区',days=7))
        weather_data = weather_data[['fxDate','tempMax','tempMin','textDay','textNight']].to_json(force_ascii=False,orient='records')

        # 水质数据
        waterqa_data = get_waterqa_now()

        agt = ollmAgent(session_id)
        agt.load_session_history(weather_data,waterqa_data)

        # 数据库检索相关文档
        docs = retriever.get_relevant_documents(user_input)
        context = '\n'.join([doc.page_content for doc in docs])
        # print(context)
        
        # 问题
        agt.messages.append({
            'role':'user',
            'content':f"""
            请根据上下文回答问题。上下文若包含答案则根据上下文回复问题，不额外扩展或添加其他响应；上下文若不包含答案，则直接回复"我暂时无法回答这个问题"。
            上下文：{context}
            问题：{user_input}
            """
        })

        # 回答
        assistant_message = ""
        response_content = ""
        for part in agt.client.chat(model=agt.model,messages=agt.messages,stream=True):
            assistant_message += part['message']['content']
            response_content += part['message']['content']
            if len(assistant_message) > 20:
                # 以SSE格式返回数据
                yield f"{assistant_message}"
                assistant_message = ''
        yield f"{assistant_message}\n\n"

        # 记录历史对话
        agt.messages.append({
            'role':'assistant',
            'content':response_content
        })
        # agt.save_session_history()

    except Exception as e:
        yield f"发生错误: {str(e)}\n\n"

app = Flask(__name__)
@app.route('/api/aiqa_local_stream',methods=['GET'])
def crab_knowledge_api():
    try:
        # read parameters
        session_id = request.args.get('session_id')
        user_input = request.args.get('user_input')

        if not session_id:
            response = json.dumps({'error':'缺少参数','code':400}, ensure_ascii=False)  # 显式指定编码
            return response
        if not user_input:
            response = json.dumps({'error':'缺少参数','code':400}, ensure_ascii=False)
            return response
        
        # QA        
        return Response(
            quary_on_local_knowdge_with_ollama(session_id,user_input),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            })
    
    except Exception as e:        
        response = json.dumps({'status':'error',
                               'message':str(e),
                               'traceback': traceback.format_exc(),
                               'code':500}, ensure_ascii=False)
        return response
    
@app.route('/api/health',methods=['GET'])
def health():
    response = json.dumps({'status':'ok',
                            'code':200}, ensure_ascii=False)
    return response
    
if __name__ == '__main__':
    # 加载数据库
    db_faiss_path = r'D:\pymethods\local_knowledge_LLM\vectorstore\db_crab_knowledge_v2'
    retriever = load_db(db_faiss_path)

    app.run(debug=True,host='0.0.0.0',port=8091)
