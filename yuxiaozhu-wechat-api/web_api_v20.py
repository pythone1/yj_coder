import traceback
import json
import base64

from flask import Flask, request, Response
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
import pandas as pd

from clients import * 


def load_db(db_faiss_path):
    ''' 加载数据库 '''
    embeddings = HuggingFaceEmbeddings(model_name = 'sentence-transformers/all-mpnet-base-v2')
    db = FAISS.load_local(db_faiss_path,embeddings,allow_dangerous_deserialization=True)

    return db.as_retriever(search_kwargs={'k':10})    

def quary_on_local_knowledge_with_ollama(session_id,user_input):
    ''' 
    基于ollama的本地知识问答
    session_id：str 任务id,用于记录、查询历史对话内容。唯一
    user_input: str 用户提问
    tools_result: str 工具调用反馈结果
    '''
    try:
        # 天气
        # weather_data = pd.DataFrame(get_weather_daypred(location='101190103',days=7))
        # weather_data = weather_data[['fxDate','tempMax','tempMin','textDay','textNight']].to_json(force_ascii=False,orient='records')
        weather_data = get_weather_daypred_from_sql(days=7)
        if weather_data['code']!=200:
            weather_data = '天气数据获取失败'
        else:
            weather_data = pd.DataFrame(weather_data['rows'])
            weather_data = weather_data[['createTime','tempMax','tempMin','textDay']].to_json(force_ascii=False,orient='records')
        
        # 水质数据
        waterqa_data = get_waterqa_now()   
        if waterqa_data['code']!=200:
            waterqa_data = '水质数据获取失败'
        else:
            waterqa_data = pd.DataFrame(waterqa_data['rows'])
            waterqa_data = waterqa_data[['createTime','temp','ph','doval','nh4']].to_json(force_ascii=False,orient='records')    

        agt = ollmAgent(session_id,model='deepseek-r1:8b')        
        agt.load_session_history(weather_data,waterqa_data)

        # 数据库检索相关文档
        docs = retriever.get_relevant_documents(user_input)
        context = '\n'.join([doc.page_content for doc in docs])
        
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

def quary_with_openai(session_id,user_input,append_files):
    '''
    基于openai的本地知识问答
    '''
    try:
        # 创建助手
        agt = openaiAgent(session_id)
        agt.load_session_history()

        # 问答
        content = [{
        'type':'text',
        'text':user_input
        }]
        for f in append_files.split(','):
            content.append({
                'type':'image_url',
                'image_url':{'url':f"data:image/jpeg;base64,{encode_image(f)}"}
            })
        agt.messages.append({
            'role':'user',
            'content':content
        }) 

        response = agt.client.chat.completions.create(
            model=agt.model,
            messages=agt.messages,
            stream=True
        )

        # 回答
        assistant_message = ""
        response_content = ""
        for part in response:
            if part.choices[0].delta.content is not None:
                assistant_message += part.choices[0].delta.content
                response_content += part.choices[0].delta.content
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
        agt.save_session_history()

    except Exception as e:
        yield f"发生错误: {str(e)}\n\n"

app = Flask(__name__)
@app.route('/api/aiqa_local_stream',methods=['GET'])
def crab_knowledge_api():
    try:
        # read parameters
        session_id = request.args.get('session_id')
        user_input = request.args.get('user_input')
        append_files = request.args.get('append_list','')

        if not session_id:
            response = json.dumps({'error':'缺少参数','code':400}, ensure_ascii=False)  # 显式指定编码
            return response
        if not user_input:
            response = json.dumps({'error':'缺少参数','code':400}, ensure_ascii=False)
            return response
        
        if append_files:
            # 有附件用智谱API问答
            return Response(
                quary_with_openai(session_id,user_input,append_files),
                mimetype="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive"
                })

        else:
            # 无附件ollama-qwen3问答
            return Response(
                quary_on_local_knowledge_with_ollama(session_id,user_input),
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
    
if __name__ == '__main__':
    # 加载数据库
    db_faiss_path = r'D:\pymethods\local_knowledge_LLM\vectorstore\db_crab_knowledge_v3'
    retriever = load_db(db_faiss_path)

    app.run(debug=True,host='0.0.0.0',port=8091)

