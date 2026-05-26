import zhipuai
import numpy as np
from scipy.spatial.distance import cosine

# --- 0. 初始化客户端 (新版写法) ---
# 不再使用 zhipuai.api_key = "...", 而是实例化客户端
client = zhipuai.ZhipuAI(api_key="37396eda5f13401ca14d9570f52b0046.Lbsee8coUifF4b6K")  # 请替换为你自己的 Key

# --- 模拟知识库数据 (注意：这里填空字符串会导致检索不到内容，建议填入测试文本) ---
knowledge_base = [
	"""序言
“十五五”时期 (2026 2030 年）是我国基本实现社会主义现
代化夺实基础、全面发力的关键时期，也是建邺深入贯彻习近平
总书记对江苏工作系列重要讲话精神，持续完善城市功能、不断
提升综合能级，全面推进中国式现代化建邺新实践的关键时期。
科学编制和实施“十五五”规划，对于全面落实党的战略部署、谱
写中匡式现代化建邺新篇章意义重大，须立足区情特征，主动全
面融入全国全省全市发展大局，科学谋划经济社会发展目标，错
定高质量发展首要任务，因地制宜发展新质生产力，统筹推进深
层次改革和高水平开放，系统推进重大战略任务、重大改革举措、
重大项目工程，为中国式现代化南京新实践贡献更多建邺力量。
根据《中共建邺区委关于制定建邺区国民经济和社会发展第
十五个五年规划的建议》，编制《建邺区国民经济和社会发展第
十五个五年规划纲要》，主要阐明“十五五”时期的发展思路、主
要目标和重点任务，是市场主体的行为导向，是政府履行职责的
重要依据，是指导建邺未来五年发展的宏伟蓝图和行动纲领。
规划期为 2026 2030 年，远期展望到 2035 年。"""
]


# --- 第一步：向量化 ---
def get_embeddings(texts):
	"""
	调用智谱 Embedding API 将文本转为向量
	"""
	try:
		response = client.embeddings.create(
			model="embedding-2",  # 使用智谱的 Embedding 模型
			input=texts
		)
		# 新版 SDK 返回的是对象结构，不是字典
		return [item.embedding for item in response.data]
	except Exception as e:
		print(f"Embedding API 调用出错: {e}")
		return []


print("正在处理知识库...")
# 这里的 knowledge_base 不要为空，否则无法检索
chunks = knowledge_base
vectors = get_embeddings(chunks)

if not vectors:
	print("错误：向量生成失败，请检查 API Key 或网络。")
	exit()


# --- 第二步：检索 ---
def search_related_docs(query, top_k=2):
	"""
	根据用户问题，在知识库中搜索最相似的片段
	"""
	# 1. 将问题向量化
	query_embedding_list = get_embeddings([query])
	if not query_embedding_list:
		return []
	query_vector = query_embedding_list[0]
	
	# 2. 计算相似度
	distances = []
	for vector in vectors:
		dist = cosine(query_vector, vector)
		distances.append(dist)
	
	# 3. 获取最相似的结果索引
	top_k_indices = np.argsort(distances)[:top_k]
	
	# 4. 返回对应的文本片段
	related_docs = [chunks[i] for i in top_k_indices]
	return related_docs


# --- 第三步：生成 (RAG的核心调用) ---
def ask_with_rag(question):
	# 1. 检索相关上下文
	context_docs = search_related_docs(question)
	context = "\n".join(context_docs)
	
	print(f"\n[系统提示] 检索到的相关内容:\n{context}\n")
	
	# 2. 构建 Prompt
	messages = [
		{
			"role": "system",
			"content": f"你是一个智能助手。请仅根据下面的【已知信息】来回答用户的问题。如果在已知信息中找不到答案，请直接回答“知识库中没有提到相关内容”，不要编造。\n\n【已知信息】:\n{context}"
		},
		{
			"role": "user",
			"content": question
		}
	]
	
	# 3. 调用 GLM-4 (新版 SDK 写法)
	try:
		response = client.chat.completions.create(
			model="glm-4",  # 或 glm-4-flash, glm-4-plus
			messages=messages,
		)
		# 新版 SDK 获取回复的方式
		return response.choices[0].message.content
	except Exception as e:
		return f"GLM-4 调用出错: {e}"

if __name__ == "__main__":
	user_question = "总书记发言的内容你知道吗"
	answer = ask_with_rag(user_question)
	print(f"用户提问: {user_question}")
	print(f"模型回答: {answer}")
