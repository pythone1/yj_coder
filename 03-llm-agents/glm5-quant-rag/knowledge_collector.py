"""
项目名称: glm5-quant-rag
技术领域: 03-llm-agents
模块说明: knowledge_collector.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

import json
import os
import pickle
import re
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
import requests
from prompts import build_collector_prompt
from zhipu_client import chat_completion


BASE_DIR = Path(__file__).resolve().parent
ENTITIES_FILE = BASE_DIR / "entities.yaml"
EVENTS_DB = BASE_DIR / "events.db"
KB_DIR = BASE_DIR / "knowledge_base"
KB_CHUNKS_FILE = KB_DIR / "zhipu_chunks.pkl"
HTTP = requests.Session()
HTTP.trust_env = False


def load_entities():
    text = ENTITIES_FILE.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        try:
            import yaml

            data = yaml.safe_load(text)
        except Exception as exc:
            raise RuntimeError(f"Cannot parse entities.yaml: {exc}") from exc
    return data.get("entities", {})


def connect():
    return sqlite3.connect(EVENTS_DB)


def init_db():
    KB_DIR.mkdir(exist_ok=True)
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                entity_id TEXT,
                symbol TEXT,
                source TEXT NOT NULL,
                event_type TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT,
                url TEXT,
                importance INTEGER DEFAULT 50,
                impact TEXT DEFAULT 'neutral',
                payload_json TEXT,
                verified INTEGER DEFAULT 0,
                UNIQUE(source, url, title)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collected_at TEXT NOT NULL,
                event_date TEXT,
                entity_id TEXT NOT NULL,
                symbol TEXT,
                source TEXT NOT NULL,
                source_type TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT,
                url TEXT,
                content TEXT,
                importance INTEGER DEFAULT 50,
                verified INTEGER DEFAULT 0,
                UNIQUE(entity_id, source, url, title)
            )
            """
        )
        for table in ["events", "knowledge_items"]:
            cols = [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
            if "verified" not in cols:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN verified INTEGER DEFAULT 0")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_entity ON knowledge_items(entity_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_collected ON knowledge_items(collected_at DESC)")


def add_event(item):
    with connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO events
            (ts, entity_id, symbol, source, event_type, title, summary, url, importance, impact, payload_json, verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.get("event_date") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                item.get("entity_id", ""),
                item.get("symbol", ""),
                item.get("source", "collector"),
                item.get("source_type", "news"),
                item.get("title", ""),
                item.get("summary", ""),
                item.get("url", ""),
                int(item.get("importance") or 50),
                item.get("impact", "neutral"),
                json.dumps(item, ensure_ascii=False),
                int(item.get("verified") or 0),
            ),
        )


def add_knowledge_item(item):
    with connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO knowledge_items
            (collected_at, event_date, entity_id, symbol, source, source_type, title, summary, url, content, importance, verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                item.get("event_date", ""),
                item.get("entity_id", ""),
                item.get("symbol", ""),
                item.get("source", ""),
                item.get("source_type", "news"),
                item.get("title", ""),
                item.get("summary", ""),
                item.get("url", ""),
                item.get("content", item.get("summary", "")),
                int(item.get("importance") or 50),
                int(item.get("verified") or 0),
            ),
        )


def verify_url(url):
    if not url:
        return False
    if url.startswith("local://") or url.startswith("rule://"):
        return True
    try:
        resp = HTTP.head(url, timeout=12, allow_redirects=True)
        if 200 <= resp.status_code < 400:
            return True
        if resp.status_code in (403, 405):
            resp = HTTP.get(url, timeout=15, stream=True, allow_redirects=True)
            return 200 <= resp.status_code < 400
    except Exception:
        return False
    return False


def extract_json(text):
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.S | re.I)
    if fenced:
        text = fenced.group(1).strip()
    start = text.find("[")
    end = text.rfind("]")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


def glm_search_entity(entity_id, entity, days):
    api_key = os.getenv("ZHIPUAI_API_KEY", "").strip()
    if not api_key:
        return []
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    stock_codes = ", ".join(entity.get("stock_codes", [])) or "未配置股票代码"
    keywords = ", ".join(entity.get("keywords", []) + entity.get("aliases", []))
    prompt = build_collector_prompt(entity_id, entity, days, since)
    content = chat_completion(
        messages=[{"role": "user", "content": prompt}],
        model=os.getenv("ZHIPU_MODEL", "glm-4.5-air"),
        tools=[{"type": "web_search", "web_search": {"enable": True, "search_result": True}}],
    )
    try:
        rows = extract_json(content)
    except Exception as exc:
        print(f"Cannot parse GLM collector result for {entity_id}: {exc}")
        return []
    output = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        row["entity_id"] = entity_id
        row["symbol"] = (entity.get("stock_codes") or [""])[0]
        row.setdefault("source", "glm_web_search")
        row.setdefault("source_type", "fundamental_news")
        row.setdefault("importance", 50)
        row.setdefault("impact", "unknown")
        row["verified"] = 1 if verify_url(row.get("url", "")) else 0
        output.append(row)
    return output


def make_seed_items(entity_id, entity):
    stock_codes = ", ".join(entity.get("stock_codes", [])) or "待维护"
    content = "\n".join(
        [
            f"实体：{entity.get('display_name', entity_id)}",
            f"分类：{entity.get('category', '')}",
            f"股票代码：{stock_codes}",
            f"关键词：{', '.join(entity.get('keywords', []))}",
            f"别名：{', '.join(entity.get('aliases', []))}",
            f"备注：{entity.get('notes', '')}",
        ]
    )
    return [
        {
            "entity_id": entity_id,
            "symbol": (entity.get("stock_codes") or [""])[0],
            "source": "entities.yaml",
            "source_type": "profile",
            "title": f"{entity.get('display_name', entity_id)} 基础画像",
            "summary": entity.get("notes", ""),
            "url": f"local://entities/{entity_id}",
            "content": content,
            "importance": 60,
            "impact": "neutral",
            "verified": 1,
        }
    ]


def rebuild_chunks():
    chunks = []
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT entity_id, symbol, source_type, title, summary, url, content
            FROM knowledge_items
            ORDER BY collected_at DESC, importance DESC
            LIMIT 2000
            """
        ).fetchall()
    for entity_id, symbol, source_type, title, summary, url, content in rows:
        text = "\n".join(
            [
                f"实体ID：{entity_id}",
                f"股票代码：{symbol}",
                f"资料类型：{source_type}",
                f"标题：{title}",
                f"摘要：{summary}",
                f"链接：{url}",
                f"正文：{content}",
            ]
        )
        chunks.append(text[:1600])
    with KB_CHUNKS_FILE.open("wb") as f:
        pickle.dump(chunks, f)
    return len(chunks)


def collect(days=7):
    init_db()
    entities = load_entities()
    inserted = 0
    for entity_id, entity in entities.items():
        rows = make_seed_items(entity_id, entity)
        try:
            rows += glm_search_entity(entity_id, entity, days)
        except Exception as exc:
            print(f"collector failed for {entity_id}: {exc}")
        for row in rows:
            if not row.get("title"):
                continue
            add_knowledge_item(row)
            if row.get("source_type") != "profile" and row.get("verified"):
                add_event(row)
            inserted += 1
    chunk_count = rebuild_chunks()
    return {"entities": len(entities), "items_seen": inserted, "chunks": chunk_count}


if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.getenv("COLLECT_DAYS", "7"))
    result = collect(days=days)
    print(json.dumps(result, ensure_ascii=False))
