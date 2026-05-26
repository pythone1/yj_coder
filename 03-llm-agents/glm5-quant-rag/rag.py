"""
项目名称: glm5-quant-rag
技术领域: 03-llm-agents
模块说明: rag.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

import json
import os
import pickle
from pathlib import Path

import pandas as pd
import requests


BASE_DIR = Path(__file__).resolve().parent
ENTITIES_FILE = BASE_DIR / "entities.yaml"
DB_DIR = BASE_DIR / "knowledge_base"
CHUNKS_FILE = DB_DIR / "zhipu_chunks.pkl"
INDEX_FILE = DB_DIR / "zhipu_stock.index"
HTTP = requests.Session()
HTTP.trust_env = False


def load_json_or_yaml(path):
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    try:
        import yaml

        return yaml.safe_load(text)
    except Exception as exc:
        raise RuntimeError(f"Cannot parse {path.name}. Install PyYAML or use JSON-compatible YAML. {exc}") from exc


def chunk_text(text, max_len=600):
    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + max_len])
        start += max_len
    return chunks


def build_entity_documents():
    config = load_json_or_yaml(ENTITIES_FILE)
    docs = []
    for entity_id, entity in config.get("entities", {}).items():
        lines = [
            f"实体ID：{entity_id}",
            f"名称：{entity.get('display_name', entity_id)}",
            f"分类：{entity.get('category', '')}",
            f"股票代码：{', '.join(entity.get('stock_codes', [])) or '待确认'}",
            f"关键词：{', '.join(entity.get('keywords', []))}",
            f"别名：{', '.join(entity.get('aliases', []))}",
            f"备注：{entity.get('notes', '')}",
        ]
        docs.append("\n".join(lines))
    return docs


def fetch_yahoo_history(symbol):
    code = symbol.replace(".HK", ".HK")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}?range=3mo&interval=1d"
    try:
        data = HTTP.get(url, timeout=10).json()
        result = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        quote = result["indicators"]["quote"][0]
        rows = []
        for i, ts in enumerate(timestamps):
            rows.append(
                {
                    "date": pd.to_datetime(ts, unit="s").strftime("%Y-%m-%d"),
                    "open": quote["open"][i],
                    "high": quote["high"][i],
                    "low": quote["low"][i],
                    "close": quote["close"][i],
                    "volume": quote["volume"][i],
                }
            )
        return rows
    except Exception:
        return []


def build_market_documents():
    config = load_json_or_yaml(ENTITIES_FILE)
    docs = []
    for entity in config.get("entities", {}).values():
        for symbol in entity.get("stock_codes", []):
            rows = fetch_yahoo_history(symbol)
            for row in rows[-30:]:
                docs.append(
                    f"{symbol} 在 {row['date']} 开盘 {row['open']}，最高 {row['high']}，"
                    f"最低 {row['low']}，收盘 {row['close']}，成交量 {row['volume']}。"
                )
    return docs


def save_chunks(chunks):
    DB_DIR.mkdir(exist_ok=True)
    with CHUNKS_FILE.open("wb") as f:
        pickle.dump(chunks, f)


def try_build_faiss(chunks):
    api_key = os.getenv("ZHIPUAI_API_KEY", "").strip()
    if not api_key:
        if INDEX_FILE.exists():
            INDEX_FILE.unlink()
        print("No ZHIPUAI_API_KEY. Saved chunks only, skipped FAISS embeddings.")
        return False
    try:
        import faiss
        import numpy as np
        from langchain_community.embeddings import ZhipuAIEmbeddings
    except Exception as exc:
        if INDEX_FILE.exists():
            INDEX_FILE.unlink()
        print(f"FAISS or embedding dependencies unavailable: {exc}")
        return False

    os.environ["ZHIPUAI_API_KEY"] = api_key
    embeddings_model = ZhipuAIEmbeddings(model="embedding-3", dimensions=1024)
    embeddings = embeddings_model.embed_documents(chunks)
    matrix = np.array(embeddings).astype("float32")
    index = faiss.IndexFlatL2(matrix.shape[1])
    index.add(matrix)
    faiss.write_index(index, str(INDEX_FILE))
    return True


if __name__ == "__main__":
    docs = build_entity_documents() + build_market_documents()
    chunks = []
    for doc in docs:
        chunks.extend(chunk_text(doc))
    save_chunks(chunks)
    built_index = try_build_faiss(chunks)
    print(f"RAG chunks: {len(chunks)} -> {CHUNKS_FILE}")
    print(f"FAISS index: {'updated' if built_index else 'skipped'}")
