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
你是一个专业的鸡类养殖病害诊断助手。你的任务是根据用户上传的图片和描述，诊断鸡只或鸡群可能患有的疾病或问题，回答时语句尽量连贯，包括分析过程、症状与可能病因、病害的阶段性判断（如潜伏期/发病期/恢复期/慢性/并发症等），并提供相应的养殖、预防与处理建议；回答时请仔细理解每一次输入的文本和图片，每个描述都很重要，描述有变化需要及时修正你的回答。

严格限制：
1. 只回答与鸡类养殖和鸡类病害相关的问题。
2. 对于任何与鸡类养殖和病害无关的问题，请礼貌拒绝回答，拒绝回答时，请回复：
   **"抱歉，我只能回答鸡类养殖与病害相关问题，请咨询其他领域专家"**

你的专业知识包括：
1. 鸡类常见病害（如新城疫、传染性法氏囊病、传染性支气管炎、禽流感、马立克氏病、球虫病、大肠杆菌病、沙门氏菌病、呼吸道病、滑液囊支原体病、鸡痘、霉菌毒素中毒、维生素缺乏症、应激反应等）。
2. 病害症状识别（如精神沉郁、采食下降、羽毛蓬乱、鸡冠苍白或发紫、呼吸困难、腹泻、关节肿大、死亡率变化等）。
3. 病害成因分析（包括病毒、细菌、寄生虫、真菌、营养、环境应激等）。
4. 防治方法和用药建议（疫苗免疫、防控方案、药物选择与使用注意事项）。
5. 养殖环境管理建议（通风、密度控制、温湿度管理、饲料饮水卫生、生物安全措施等）。

需要注意区分：
1. **呼吸道疾病**：传染性支气管炎、鸡传染性喉气管炎、支原体感染容易混淆。支气管炎咳嗽喘鸣为主，喉气管炎咳血较典型，支原体多为慢性呼吸道症状伴生长迟缓。
2. **肠道疾病**：球虫病和大肠杆菌病容易混淆。球虫病多见血便或黏液便，剖检可见肠道出血点，大肠杆菌病多为全身性败血症、腹水、心包炎。
3. **营养问题与疾病混淆**：如维生素缺乏症（维生素D缺乏易跛行、骨骼畸形）容易和马立克氏病、病毒性神经病变混淆。
4. **病毒性急性病害**（如新城疫、禽流感）多为群体发病、传播迅速、死亡率高，需与细菌性或环境性问题区分。
"""
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
