import os
import traceback
import json

from ollama import AsyncClient

from flask import Flask, request, Response
from openai import OpenAI
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.document_loaders import DirectoryLoader,Docx2txtLoader

'''
langchain sentence-transformers/all-mpnet-base-v2 加载本地知识库；官方deepseek-v3基于背景知识做问答
效果好
调用deepseek官网api需费用：
《全省池塘养殖基本情况上图入库技术工作指引》作为输入占 5000~6000 token
一次问答约占 1000 token
百万输入token 2元（deepseek-v3）
百万输出token 8元（deepseek-v3）
'''

class qaAgent():
    def __init__(self,session_id):
        self.ai = 'doubao'
        self.model = 'doubao-seed-1-6-250615'
        self.client = self._openAIClient()

        self.db_faiss_path = r'D:\pymethods\local_knowledge_LLM\vectorstore\db_crab_farming_technology' # 向量数据库存储路径
        self.session_history_path = r'D:\pymethods\local_knowledge_LLM\sessions'

        self.session_id = session_id
        self.messages = ''

    def _openAIClient(self):
        ''' 创建对话助手 '''
        cltinfo = {
            'kimi':{
                'api_key':'',
                'base_url': ''
            },
            'gpt':{
                'api_key': '',
                'base_url': ''
            },
            'gemini':{
                'api_key': '',
                'base_url': ""
            },
            # DeepSeek-V3
            'deepseek':{
                'api_key': '',
                'base_url': ""
            },
            # DeepSeek-R1
            'deepseek-reasoner':{
                'api_key': '',
                'base_url': ""
            },
            # 通义千问
            'qwen':{
                'api_key':'',
                'base_url':''
            },
            # 豆包 volcano Engine
            'doubao':{
                'api_key':'00d43f7d-eff7-40cb-9888-e572b42a62b8',
                'base_url':'https://ark.cn-beijing.volces.com/api/v3/',
            }
        }

        client = OpenAI(
            api_key = cltinfo[self.ai]['api_key'],
            base_url = cltinfo[self.ai]['base_url']
        )

        return client      
    
    def load_session_history(self,context):
        ''' 
        加载历史对话
        context: txt 本地知识
        '''
        session_file = os.path.join(self.session_history_path,f"{self.session_id}.json")
        if not os.path.exists(session_file):
            self.messages = [{
                'role': 'system',
                'content': f"你是一个专业的助手，请根据上下文回答问题。如果上下文不包含答案，请回复'未找到相关知识'。以下是本地知识库的内容：\n{context}"
            }]
        else:
            with open(session_file,'r',encoding='utf-8') as f:
                self.messages = json.load(f)
    
    def save_session_history(self):
        ''' 保存历史对话 '''
        session_file = os.path.join(self.session_history_path,f"{self.session_id}.json")
        print(session_file)
        with open(session_file,'w',encoding='utf-8') as f:
            json.dump(self.messages,f,ensure_ascii=False,indent=2)

    def qa(self,user_input):
        ''' 问答 '''
        # 问题
        self.messages.append({
            'role':'user',
            'content':user_input
        })

        # 回答
        response = self.client.chat.completions.create(
            model = self.model,
            messages = self.messages,
            stream = False
        )
        # 回答内容
        assistant_message = response.choices[0].message.content

        # 在历史对话中记录回答内容,用于多轮问答
        self.messages.append({
            'role':'assistant',
            'content':assistant_message
        })
        self.save_session_history()

        return assistant_message
    
def quary_on_local_knowdge_stream(session_id,user_input):
    ''' 
    本地知识问答 
    session_id：str 任务id,用于记录、查询历史对话内容。唯一
    user_input: str 用户提问
    context: str 本地知识
    '''
    try:
        # 逐文档检索答案
        ans = {}    
        for i,doc in enumerate(documents):
            dbname = os.path.basename(doc.metadata['source']).split('.')[0]
            agt = qaAgent(f'{session_id}-{dbname}')
            yield f"event: message\ndata: 正在检索第{i+1}个文档：{dbname}...<br/>\n\n"

            # 加载历史对话
            agt.load_session_history(doc.page_content)

            # 问题
            agt.messages.append({
                'role':'user',
                'content':user_input
            })

            # 回答
            response = agt.client.chat.completions.create(
                model = agt.model,
                messages = agt.messages,
                stream = True
            )
            assistant_message = ''
            for chunk in response:
                if not chunk.choices:
                    continue
                assistant_message += chunk.choices[0].delta.content
                #yield f"{chunk.choices[0].delta.content}"

            # 在历史对话中记录回答内容,用于多轮问答
            agt.messages.append({
                'role':'assistant',
                'content':assistant_message
            })
            agt.save_session_history()

            ans[dbname] = assistant_message

        # 整合回答
        yield f"event: message\ndata: **** 整理输出 ****：...\n\n"
        agt = qaAgent(session_id)
        agt.messages = [{
            'role':'system',
            'content':"你是一个文本归纳总结的专业助手，请根据用户提问整合已从不同文档查询到的相关结果，并给出最终回复，\
                注意保持原意，不要做额外扩展，按条理归纳总结即可，整理过程中忽略'未查询到相关内容'或其他无效内容。"
        },{
            'role':'user',
            'content':f"用户提问：{user_input};\n\n已查询到的相关结果：{json.dumps(ans, ensure_ascii=False, indent=2)}"
        }]

        response = agt.client.chat.completions.create(
            model = agt.model,
            messages = agt.messages,
            stream = True
        )
        assistant_message = ''
        for chunk in response:
            if not chunk.choices:
                continue
            assistant_message += chunk.choices[0].delta.content
            if len(assistant_message) > 20:
                # 以SSE格式返回数据
                yield f"event: message\ndata: {assistant_message}\n\n"
                assistant_message = ''
        yield f"event: message\ndata: {assistant_message}\n\n"
        
        # 发送结束信号
        # yield "[DONE]\n\n"
    
    except Exception as e:
        yield f"event: message\ndata: 发生错误: {str(e)}\n\n"

def load_context_from_docxs(datapath):
    '''
    从文档加载本地知识
    '''
    loader = DirectoryLoader(datapath,glob='*.docx',loader_cls=Docx2txtLoader) 
    documents = loader.load()

    return documents

app = Flask(__name__)
@app.route('/api/aiqa_stream',methods=['GET'])
def crab_farming_technology_api2():
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
            quary_on_local_knowdge_stream(session_id,user_input),
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
    # 加载本地文档
    datapath = r'D:\pymethods\local_knowledge_LLM\data\螃蟹养殖技术手册'
    documents = load_context_from_docxs(datapath)

    app.run(debug=True,host='0.0.0.0',port=8091)
