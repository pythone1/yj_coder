import base64
import os
from flask import Flask, request, jsonify, render_template
from zai import ZhipuAiClient

# ====== 1. 初始化配置 ====== #
client = ZhipuAiClient(api_key="37396eda5f13401ca14d9570f52b0046.Lbsee8coUifF4b6K")
MODEL_NAME = "glm-4.5v"

app = Flask(__name__)

# ====== 2. 保存会话历史 ====== #
# 格式： {"session_id": [messages...]}
session_store = {}
# ====== 限制上下文长度 ====== #
MAX_TURNS = 10
def trim_session(session_id):
    """
    裁剪会话，只保留 system 提示 + 最近 N 轮对话
    """
    messages = session_store[session_id]
    # system 在第0条，其余是 user/assistant 交替
    system_msg = messages[0]
    other_msgs = messages[1:]
    # 每一轮包含 user + assistant，所以 MAX_TURNS * 2
    max_len = MAX_TURNS * 2
    if len(other_msgs) > max_len:
        other_msgs = other_msgs[-max_len:]
    session_store[session_id] = [system_msg] + other_msgs

def encode_image_to_base64(file_storage):
    """读取上传的文件对象转 base64"""
    img_bytes = file_storage.read()
    return base64.b64encode(img_bytes).decode("utf-8")

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    """
    支持前端表单上传：
    form-data:
        session_id: 会话ID
        text: 问题文本
        image: 文件上传（可选）
    """
    session_id = request.form.get("session_id", "default")
    text = request.form.get("text", "")
    image_file = request.files.get("image")

    # 初始化会话存储
    if session_id not in session_store:
        session_store[session_id] = [{
		    "role": "system",
		    "content": """
你是一个专业的大闸蟹病害诊断助手。你的任务是根据用户上传的图片和描述，诊断大闸蟹可能患有的病害，回答描述时语句尽量连贯，包括分析过程及描述的病害可能存在的阶段性，并提供相应的防治建议；回答时请仔细理解每一次输入的文本和图片，每个描述都很重要，描述有变化需要及时修正你的回答。
严格限制：
1.只回答与大闸蟹病害相关的问题
2.对于任何与大闸蟹病害无关的问题，请礼貌拒绝回答，拒绝回答时，请回复："抱歉，我只能回答大闸蟹病害相关问题，请咨询其他领域专家"
你的专业知识包括:
1.大闸蟹常见病害（如黑鳃病、甲壳溃疡病、烂肢病、水肿病、肠炎病、弧菌病、弗氏柠檬酸杆菌感染症、固着类纤毛虫病、蟹奴病（臭虫蟹病）、颤抖病（支原体病）、微孢子虫病、水霉病、肝胰腺疾病、蜕壳不遂病、青泥苔病等）
2.病害症状识别
3.病害成因分析
4.防治方法和用药建议
5.养殖环境管理建议
需要注意区分：
1、水霉病和纤毛虫病容易错，都有附着物，水霉病是白颜色，纤毛虫病是黄绿色
2、烂肢病和弧菌病容易错，烂肢病患病河蟹腹部和附肢容易发生腐烂，腹部出现灰黄或灰黑色斑点，肛门红肿，行动迟缓，出现摄食能力下降甚至不进食现象，蜕壳困难最终导致死亡。弧菌病腹部和附肢腐烂，食欲下降，身体颜色变浅，发育蜕壳迟缓，喜欢匍匐于岸边直至死亡，死亡和濒临死亡的病蟹体内有大量凝血块
3、肝胰腺疾病的特点主要体现在肝胰腺腐烂坏死，得病导致甲壳上附着大量有机碎屑、藻类、原生动物等，注意和纤毛虫病区分它不会附着大量有机碎屑、藻类、原生动物等"""
	    }]
    content = []
    if image_file:
        image_base64 = encode_image_to_base64(image_file)
        image_data_uri = f"data:image/png;base64,{image_base64}"
        content.append({
            "type": "image_url",
            "image_url": {"url": image_data_uri}
        })

    if text:
        content.append({"type": "text", "text": text})

    # 用户消息入栈
    session_store[session_id].append({
        "role": "user",
        "content": content
    })

    # 调用智谱 API
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=session_store[session_id],
        thinking={"type": "enabled"}
    )
    reply_msg = response.choices[0].message
    print("原始 reply_msg:", reply_msg)
    
    text_content = getattr(reply_msg, "content", "") or ""
    reply_dict = {
	    "role": getattr(reply_msg, "role", "assistant"),
	    "content": [{"type": "text", "text": text_content}]
    }
    print("解析后的 reply_dict:", reply_dict)
    # 保存助手回复到上下文
    session_store[session_id].append(reply_dict)
    trim_session(session_id)
    return jsonify({
	    "reply": reply_dict,
	    "session_messages": session_store[session_id]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
