import os

from langchain.document_loaders import DirectoryLoader,PyPDFLoader,Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings


# 创建向量数据库
def create_vector_db(data_path,db_faiss_path):
    '''
    创建向量数据库
    data_path: pdf数据路径
    db_faiss_path: 向量数据库保存路径
    '''
    # 加载文档
    # DirectoryLoader可以快速将系统中的文件读取的LangChain文档对象，通过loader_cls参数指定加载器类
    # loader = DirectoryLoader(data_path,glob="*.pdf",loader_cls=PyPDFLoader) 
    loader = DirectoryLoader(data_path,glob="*养殖期间常见问题及解决方案.docx",loader_cls=Docx2txtLoader) 
    documents = loader.load()
    # documents_content = documents[0].page_content # 文档内容

    # 文本分割
    # 核心思想是根据一组分隔符（separators）逐步分割文本，直到每个块的大小都符合预设的chunk_size，默认提供给它的字符包括["\n\n", "\n", " ", ""]
    # 递归分割：先按段落分割（\n\n），段落过长再按句子分割（\n），句子过长则按空格分割单词，最后按单个字符分割
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500,chunk_overlap=50)
    texts = text_splitter.split_documents(documents)

    # 使用HuggingFace嵌入模型
    embeddings = HuggingFaceBgeEmbeddings(model_name='sentence-transformers/all-mpnet-base-v2')

    # 创建并保存向量数据库
    # 结合了 FAISS（Facebook AI Similarity Search）和文档数据，用于创建一个向量索引
    db = FAISS.from_documents(texts,embeddings)
    db.save_local(db_faiss_path)
    print("向量数据库创建完成并已保存")

# 加载本地知识库
def initialize_vector_db(db_faiss_path):
    embeddings = HuggingFaceEmbeddings(model_name = 'sentence-transformers/all-mpnet-base-v2')
    db = FAISS.load_local(db_faiss_path,embeddings,allow_dangerous_deserialization=True)

    return db

if __name__ == '__main__':
    # 配置
    data_path = r'D:\pymethods\local_knowledge_LLM\data\螃蟹养殖技术手册' # 存放知识文档的目录
    db_faiss_path = r'D:\pymethods\local_knowledge_LLM\vectorstore\db_crab_farming_QA' # 向量数据库存储路径

    create_vector_db(data_path,db_faiss_path)
    