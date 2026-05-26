import json
import os
import pickle
import subprocess
import sys
import sqlite3
import tempfile
import threading
import time
import http.server
import socketserver
from collections import deque
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pandas as pd
import requests
from prompts import build_analyst_prompt
from zhipu_client import chat_completion


BASE_DIR = Path(__file__).resolve().parent
ENTITIES_FILE = BASE_DIR / "entities.yaml"
DATA_FILE = BASE_DIR / "zhipu_data.json"
EVENTS_DB = BASE_DIR / "events.db"
KB_CHUNKS_FILE = BASE_DIR / "knowledge_base" / "zhipu_chunks.pkl"

HOST = os.getenv("APP_HOST", "")
PORT = int(os.getenv("APP_PORT", "8888"))
REFRESH_SECONDS = int(os.getenv("REFRESH_SECONDS", "15"))
DAILY_COLLECT_HOUR = int(os.getenv("DAILY_COLLECT_HOUR", "7"))
COLLECT_DAYS = int(os.getenv("COLLECT_DAYS", "7"))
ZHIPU_API_KEY = os.getenv("ZHIPUAI_API_KEY", "").strip()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "http://finance.sina.com.cn/",
}
HTTP = requests.Session()
HTTP.trust_env = False

state_lock = threading.Lock()
app_state = {
    "updated_at": None,
    "entities": {},
    "stocks": {},
    "theme_scores": [],
    "events": [],
    "system": {},
}
trade_tapes = {}


def now_iso():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_json_or_yaml(path):
    if not path.exists():
        return {"entities": {}}
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    try:
        import yaml

        return yaml.safe_load(text) or {"entities": {}}
    except Exception as exc:
        raise RuntimeError(f"Cannot parse {path.name}. Install PyYAML or use JSON-compatible YAML. {exc}") from exc


def load_entities():
    raw = load_json_or_yaml(ENTITIES_FILE)
    entities = raw.get("entities", {})
    for entity_id, entity in entities.items():
        entity.setdefault("id", entity_id)
        entity.setdefault("display_name", entity_id)
        entity.setdefault("stock_codes", [])
        entity.setdefault("keywords", [])
        entity.setdefault("aliases", [])
        entity.setdefault("category", "")
        entity.setdefault("notes", "")
    return entities


def hk_code(symbol):
    return symbol.upper().replace(".HK", "").zfill(5)


def normalize_symbol(symbol):
    symbol = symbol.strip().upper()
    if symbol.endswith(".HK"):
        return f"{hk_code(symbol)}.HK"
    if symbol.isdigit():
        return f"{symbol.zfill(5)}.HK"
    return symbol


def calculate_indicators(df):
    if df.empty:
        return df
    for col in ["open", "close", "high", "low", "vol"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "close" not in df.columns:
        return df.fillna(0)

    df["MA5"] = df["close"].rolling(5).mean()
    df["MA10"] = df["close"].rolling(10).mean()
    df["MA20"] = df["close"].rolling(20).mean()
    df["STD20"] = df["close"].rolling(20).std()
    df["UPPER"] = df["MA20"] + 2 * df["STD20"]
    df["LOWER"] = df["MA20"] - 2 * df["STD20"]

    exp12 = df["close"].ewm(span=12, adjust=False).mean()
    exp26 = df["close"].ewm(span=26, adjust=False).mean()
    df["DIF"] = exp12 - exp26
    df["DEA"] = df["DIF"].ewm(span=9, adjust=False).mean()
    df["MACD"] = (df["DIF"] - df["DEA"]) * 2

    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss.replace(0, pd.NA)
    df["RSI"] = 100 - (100 / (1 + rs))
    return df.fillna(0)


class EventStore:
    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        self.init_db()

    def connect(self):
        return sqlite3.connect(self.path)

    def init_db(self):
        with self.connect() as conn:
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
            cols = [row[1] for row in conn.execute("PRAGMA table_info(events)").fetchall()]
            if "verified" not in cols:
                conn.execute("ALTER TABLE events ADD COLUMN verified INTEGER DEFAULT 0")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_entity ON events(entity_id)")

    def add_event(self, event):
        event = {
            "ts": event.get("ts") or now_iso(),
            "entity_id": event.get("entity_id", ""),
            "symbol": event.get("symbol", ""),
            "source": event.get("source", "system"),
            "event_type": event.get("event_type", "note"),
            "title": event.get("title", ""),
            "summary": event.get("summary", ""),
            "url": event.get("url", ""),
            "importance": int(event.get("importance", 50)),
            "impact": event.get("impact", "neutral"),
            "payload_json": json.dumps(event.get("payload", {}), ensure_ascii=False),
            "verified": int(event.get("verified", 1)),
        }
        if not event["title"]:
            return
        with self.lock, self.connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO events
                (ts, entity_id, symbol, source, event_type, title, summary, url, importance, impact, payload_json, verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event["ts"],
                    event["entity_id"],
                    event["symbol"],
                    event["source"],
                    event["event_type"],
                    event["title"],
                    event["summary"],
                    event["url"],
                    event["importance"],
                    event["impact"],
                    event["payload_json"],
                    event["verified"],
                ),
            )

    def list_events(self, entity_id=None, limit=50):
        sql = """
            SELECT ts, entity_id, symbol, source, event_type, title, summary, url, importance, impact, verified
            FROM events
        """
        params = []
        if entity_id:
            sql += " WHERE entity_id = ?"
            params.append(entity_id)
        sql += " ORDER BY ts DESC LIMIT ?"
        params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        keys = ["ts", "entity_id", "symbol", "source", "event_type", "title", "summary", "url", "importance", "impact", "verified"]
        return [dict(zip(keys, row)) for row in rows]


event_store = EventStore(EVENTS_DB)


class MarketProvider:
    def fetch_realtime(self, symbol):
        code = hk_code(symbol)
        url = f"http://hq.sinajs.cn/list=rt_hk{code}"
        resp = HTTP.get(url, headers=HEADERS, timeout=4)
        resp.encoding = "gbk"
        parts = resp.text.split('"')
        if len(parts) < 2 or not parts[1]:
            raise RuntimeError(f"empty realtime response for {symbol}")
        arr = parts[1].split(",")
        if len(arr) < 12:
            raise RuntimeError(f"invalid realtime response for {symbol}")
        return {
            "symbol": normalize_symbol(symbol),
            "name": arr[1] if len(arr) > 1 else normalize_symbol(symbol),
            "price": float(arr[6]),
            "prev_close": float(arr[3]),
            "open": float(arr[2]),
            "high": float(arr[4]),
            "low": float(arr[5]),
            "vol": float(arr[11]),
            "pct": float(arr[8]),
            "bid": [float(arr[9]), 0],
            "ask": [float(arr[10]), 0],
        }

    def fetch_intraday(self, symbol, realtime):
        code = hk_code(symbol)
        url = f"http://web.ifzq.gtimg.cn/appstock/app/minute/query?code=hk{code}"
        data = HTTP.get(url, headers=HEADERS, timeout=5).json()
        rows = data["data"][f"hk{code}"]["data"]["data"]
        times, prices, vwaps, net_vols = [], [], [], []
        total_v, total_amt = 0.0, 0.0
        for row in rows:
            parts = row.split(" ")
            if len(parts) < 3:
                continue
            minute, price, vol = parts[0], float(parts[1]), float(parts[2])
            times.append(minute[:2] + ":" + minute[2:])
            prices.append(price)
            total_v += vol
            total_amt += price * vol
            vwaps.append(round(total_amt / total_v, 3) if total_v else price)
            prev = prices[-2] if len(prices) > 1 else realtime["prev_close"]
            net_vols.append(vol if price >= prev else -vol)
        if prices and abs(prices[-1] - realtime["price"]) > 0.001:
            prices[-1] = realtime["price"]
        df = calculate_indicators(pd.DataFrame({"close": prices}))
        return {
            "times": times,
            "prices": prices,
            "vwaps": vwaps,
            "net_vols": net_vols,
            "upper": df["UPPER"].tolist() if not df.empty else [],
            "lower": df["LOWER"].tolist() if not df.empty else [],
            "macd": df["MACD"].tolist() if not df.empty else [],
            "dif": df["DIF"].tolist() if not df.empty else [],
            "dea": df["DEA"].tolist() if not df.empty else [],
        }

    def fetch_kline(self, symbol):
        code = hk_code(symbol)
        url = f"http://web.ifzq.gtimg.cn/appstock/app/hkfqkline/get?param=hk{code},day,,,80,qfq"
        data = HTTP.get(url, headers=HEADERS, timeout=5).json()
        node = data["data"][f"hk{code}"]
        rows = node.get("qfqday") or node.get("day") or []
        if not rows:
            return {}, {}
        df = pd.DataFrame([r[:6] for r in rows], columns=["date", "open", "close", "high", "low", "vol"])
        df = calculate_indicators(df)
        df["net_vol"] = df.apply(lambda r: r["vol"] if r["close"] >= r["open"] else -r["vol"], axis=1)
        last = df.iloc[-1].to_dict()
        technical = {
            "MA5": float(last.get("MA5", 0)),
            "MA10": float(last.get("MA10", 0)),
            "MA20": float(last.get("MA20", 0)),
            "MACD": float(last.get("MACD", 0)),
            "DIF": float(last.get("DIF", 0)),
            "DEA": float(last.get("DEA", 0)),
            "RSI": float(last.get("RSI", 50)),
            "UPPER": float(last.get("UPPER", 0)),
            "LOWER": float(last.get("LOWER", 0)),
        }
        kline = {
            "dates": df["date"].tolist(),
            "values": df[["open", "close", "low", "high"]].values.tolist(),
            "net_vols": df["net_vol"].tolist(),
            "ma5": df["MA5"].tolist(),
            "ma10": df["MA10"].tolist(),
            "ma20": df["MA20"].tolist(),
            "macd": df["MACD"].tolist(),
            "dif": df["DIF"].tolist(),
            "dea": df["DEA"].tolist(),
        }
        return kline, technical


market_provider = MarketProvider()


def update_trade_tape(symbol, realtime):
    tape_state = trade_tapes.setdefault(symbol, {"last_total_vol": 0, "tape": deque(maxlen=50)})
    last_total_vol = tape_state["last_total_vol"]
    if last_total_vol > 0 and realtime["vol"] > last_total_vol:
        diff = realtime["vol"] - last_total_vol
        if diff < 10000000:
            side = "Buy" if realtime["price"] >= realtime["prev_close"] else "Sell"
            tape_state["tape"].appendleft(
                {"t": time.strftime("%H:%M:%S"), "p": realtime["price"], "v": int(diff), "s": side}
            )
    tape_state["last_total_vol"] = realtime["vol"]
    return list(tape_state["tape"])


def detect_market_events(entity_id, symbol, stock_data):
    rt = stock_data.get("realtime") or {}
    tech = stock_data.get("technical") or {}
    date_key = datetime.now().strftime("%Y%m%d")
    pct = float(rt.get("pct") or 0)
    price = float(rt.get("price") or 0)
    upper = float(tech.get("UPPER") or 0)
    ma20 = float(tech.get("MA20") or 0)
    macd = float(tech.get("MACD") or 0)

    if abs(pct) >= 5:
        event_store.add_event(
            {
                "entity_id": entity_id,
                "symbol": symbol,
                "source": "market-rule",
                "event_type": "股价异动",
                "title": f"{symbol} 日内涨跌幅达到 {pct:.2f}%",
                "summary": "规则触发：涨跌幅绝对值超过 5%。",
                "url": f"rule://{date_key}/{symbol}/pct",
                "importance": min(95, 60 + int(abs(pct))),
                "impact": "positive" if pct > 0 else "negative",
            }
        )
    if upper and price > upper:
        event_store.add_event(
            {
                "entity_id": entity_id,
                "symbol": symbol,
                "source": "market-rule",
                "event_type": "技术突破",
                "title": f"{symbol} 价格突破布林上轨",
                "summary": f"现价 {price:.2f} 高于 BOLL 上轨 {upper:.2f}。",
                "url": f"rule://{date_key}/{symbol}/boll",
                "importance": 70,
                "impact": "positive",
            }
        )
    if ma20 and price > ma20 and macd > 0:
        event_store.add_event(
            {
                "entity_id": entity_id,
                "symbol": symbol,
                "source": "market-rule",
                "event_type": "趋势观察",
                "title": f"{symbol} 站上 MA20 且 MACD 为正",
                "summary": f"现价 {price:.2f}，MA20 {ma20:.2f}，MACD {macd:.3f}。",
                "url": f"rule://{date_key}/{symbol}/trend",
                "importance": 60,
                "impact": "positive",
            }
        )


def score_entity(entity_id, entity, stocks, events):
    score = 30
    drivers = []
    for symbol in entity.get("stock_codes", []):
        stock = stocks.get(normalize_symbol(symbol), {})
        rt = stock.get("realtime") or {}
        tech = stock.get("technical") or {}
        pct = float(rt.get("pct") or 0)
        rsi = float(tech.get("RSI") or 50)
        macd = float(tech.get("MACD") or 0)
        score += max(-15, min(25, pct * 1.6))
        if macd > 0:
            score += 8
            drivers.append("MACD偏强")
        if rsi >= 70:
            score += 7
            drivers.append("RSI高位")
        if abs(pct) >= 5:
            drivers.append(f"{symbol} 涨跌幅 {pct:.2f}%")
    entity_events = [e for e in events if e.get("entity_id") == entity_id]
    if entity_events:
        score += min(25, sum(int(e.get("importance") or 0) for e in entity_events[:5]) / 20)
        drivers.append(f"近事件 {len(entity_events)} 条")
    score = round(max(0, min(100, score)), 1)
    if score >= 75:
        level = "强关注"
    elif score >= 55:
        level = "观察"
    else:
        level = "低热度"
    return {
        "entity_id": entity_id,
        "display_name": entity.get("display_name", entity_id),
        "score": score,
        "level": level,
        "drivers": drivers[:4],
    }


def atomic_write_json(path, data):
    fd, tmp_name = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)


def refresh_loop():
    print(f"[{now_iso()}] research terminal starting, refresh={REFRESH_SECONDS}s")
    while True:
        try:
            entities = load_entities()
            stocks = {}
            errors = []
            symbol_to_entity = {}
            for entity_id, entity in entities.items():
                for symbol in entity.get("stock_codes", []):
                    symbol_to_entity[normalize_symbol(symbol)] = entity_id

            for symbol, entity_id in symbol_to_entity.items():
                try:
                    realtime = market_provider.fetch_realtime(symbol)
                    intraday = market_provider.fetch_intraday(symbol, realtime)
                    kline, technical = market_provider.fetch_kline(symbol)
                    stock_data = {
                        "entity_id": entity_id,
                        "symbol": symbol,
                        "realtime": realtime,
                        "tape": update_trade_tape(symbol, realtime),
                        "intraday": intraday,
                        "kline": kline,
                        "technical": technical,
                        "status": "ok",
                    }
                    detect_market_events(entity_id, symbol, stock_data)
                    stocks[symbol] = stock_data
                except Exception as exc:
                    errors.append(f"{symbol}: {exc}")
                    stocks[symbol] = {"entity_id": entity_id, "symbol": symbol, "status": "error", "error": str(exc)}

            recent_events = event_store.list_events(limit=80)
            theme_scores = [
                score_entity(entity_id, entity, stocks, recent_events) for entity_id, entity in entities.items()
            ]
            theme_scores.sort(key=lambda item: item["score"], reverse=True)
            new_state = {
                "updated_at": now_iso(),
                "entities": entities,
                "stocks": stocks,
                "theme_scores": theme_scores,
                "events": recent_events,
                "system": {
                    "has_zhipu_key": bool(ZHIPU_API_KEY),
                    "errors": errors[-10:],
                    "refresh_seconds": REFRESH_SECONDS,
                },
            }
            with state_lock:
                app_state.clear()
                app_state.update(new_state)
            atomic_write_json(DATA_FILE, new_state)
            print(f"[{now_iso()}] updated stocks={len(stocks)} events={len(recent_events)}")
        except Exception as exc:
            print(f"[{now_iso()}] refresh error: {exc}")
        time.sleep(REFRESH_SECONDS)


def daily_collect_loop():
    last_run_date = None
    while True:
        now = datetime.now()
        should_run = last_run_date != now.date() and (now.hour >= DAILY_COLLECT_HOUR or last_run_date is None)
        if should_run:
            try:
                print(f"[{now_iso()}] knowledge collector starting")
                result = subprocess.run(
                    [sys.executable, str(BASE_DIR / "knowledge_collector.py"), str(COLLECT_DAYS)],
                    cwd=str(BASE_DIR),
                    capture_output=True,
                    text=True,
                    timeout=600,
                )
                if result.returncode == 0:
                    print(f"[{now_iso()}] knowledge collector done: {result.stdout.strip()}")
                else:
                    print(f"[{now_iso()}] knowledge collector failed: {result.stderr.strip()}")
                last_run_date = now.date()
            except Exception as exc:
                print(f"[{now_iso()}] knowledge collector error: {exc}")
                last_run_date = now.date()
        time.sleep(300)


def load_kb_chunks():
    if not KB_CHUNKS_FILE.exists():
        return []
    try:
        with KB_CHUNKS_FILE.open("rb") as f:
            chunks = pickle.load(f)
        return [str(chunk) for chunk in chunks]
    except Exception:
        return []


def lexical_search(query, chunks, limit=4):
    words = [w.lower() for w in query.replace(",", " ").replace("，", " ").split() if w.strip()]
    scored = []
    for chunk in chunks:
        low = chunk.lower()
        score = sum(low.count(word) for word in words)
        for token in ["智谱", "MiniMax", "壁仞", "壁韧", "GLM", "AI"]:
            if token.lower() in query.lower() and token.lower() in low:
                score += 3
        if score:
            scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in scored[:limit]]


def local_answer(message, selected_entity=None, selected_symbol=None):
    with state_lock:
        snapshot = json.loads(json.dumps(app_state, ensure_ascii=False))
    entities = snapshot.get("entities", {})
    stocks = snapshot.get("stocks", {})
    events = snapshot.get("events", [])
    scores = snapshot.get("theme_scores", [])

    entity = entities.get(selected_entity or "", {})
    stock = stocks.get(selected_symbol or "", {})
    if not entity and selected_entity:
        entity = entities.get(selected_entity, {})

    chunks = lexical_search(message, load_kb_chunks())
    lines = []
    lines.append("核心结论")
    if entity:
        score = next((s for s in scores if s["entity_id"] == selected_entity), None)
        if score:
            lines.append(f"- {entity.get('display_name')} 当前主题热度 {score['score']}/100，状态：{score['level']}。")
        else:
            lines.append(f"- 已选实体：{entity.get('display_name')}。")
    else:
        top = scores[0] if scores else None
        if top:
            lines.append(f"- 当前热度最高的是 {top['display_name']}，分数 {top['score']}/100。")
        else:
            lines.append("- 当前没有足够数据形成排序。")

    if stock.get("status") == "ok":
        rt = stock.get("realtime", {})
        tech = stock.get("technical", {})
        lines.append("")
        lines.append("行情/技术面")
        lines.append(
            f"- {selected_symbol}: 现价 {rt.get('price')}，涨跌幅 {rt.get('pct')}%，"
            f"RSI {tech.get('RSI', 0):.1f}，MACD {tech.get('MACD', 0):.3f}。"
        )

    related_events = [e for e in events if not selected_entity or e.get("entity_id") == selected_entity][:5]
    lines.append("")
    lines.append("关键事件")
    if related_events:
        for event in related_events:
            lines.append(f"- [{event.get('event_type')}] {event.get('title')} ({event.get('ts')})")
    else:
        lines.append("- 暂无结构化事件。")

    lines.append("")
    lines.append("本地知识库")
    if chunks:
        for chunk in chunks:
            one_line = " ".join(chunk.split())[:180]
            lines.append(f"- {one_line}")
    else:
        lines.append("- 未命中本地知识库片段。")

    lines.append("")
    lines.append("风险点")
    lines.append("- 主题映射标的需人工确认，不能把公司新闻直接等同于股票基本面。")
    lines.append("- 当前结论基于本地行情、规则事件和知识库检索，不构成投资建议。")
    return "\n".join(lines)


def call_remote_ai(message, selected_entity=None, selected_symbol=None):
    if not ZHIPU_API_KEY:
        return None
    with state_lock:
        snapshot = json.loads(json.dumps(app_state, ensure_ascii=False))
    context = {
        "selected_entity": selected_entity,
        "selected_symbol": selected_symbol,
        "theme_scores": snapshot.get("theme_scores", [])[:5],
        "stock": snapshot.get("stocks", {}).get(selected_symbol or "", {}),
        "events": snapshot.get("events", [])[:10],
        "kb_hits": lexical_search(message, load_kb_chunks(), limit=5),
    }
    prompt = build_analyst_prompt(context)
    return chat_completion(
        messages=[{"role": "system", "content": prompt}, {"role": "user", "content": message}],
        model=os.getenv("ZHIPU_MODEL", "glm-4.5-air"),
    )


def generate_report():
    with state_lock:
        snapshot = json.loads(json.dumps(app_state, ensure_ascii=False))
    lines = [f"# 港股 AI/芯片主题日报 {datetime.now().strftime('%Y-%m-%d')}", ""]
    lines.append("## 主题热度")
    for item in snapshot.get("theme_scores", [])[:10]:
        drivers = "；".join(item.get("drivers") or ["暂无驱动"])
        lines.append(f"- {item['display_name']}: {item['score']}/100，{item['level']}。{drivers}")
    lines.append("")
    lines.append("## 重点事件")
    for event in snapshot.get("events", [])[:10]:
        lines.append(f"- [{event.get('event_type')}] {event.get('title')} ({event.get('ts')})")
    lines.append("")
    lines.append("## 风险提示")
    lines.append("- 关联公司、影子股和产业链映射需要人工确认。")
    lines.append("- 自动规则只提供研究线索，不构成投资建议。")
    return "\n".join(lines)


class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True


class ResearchHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ["/api/state", "/zhipu_data.json"]:
            with state_lock:
                payload = json.loads(json.dumps(app_state, ensure_ascii=False))
            self.send_json(payload)
            return
        if parsed.path == "/api/events":
            params = parse_qs(parsed.query)
            entity_id = (params.get("entity") or [""])[0] or None
            self.send_json({"events": event_store.list_events(entity_id=entity_id, limit=100)})
            return
        if parsed.path == "/api/report":
            self.send_json({"report": generate_report()})
            return
        return super().do_GET()

    def do_POST(self):
        if self.path != "/chat":
            self.send_json({"error": "not found"}, status=404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            message = str(payload.get("msg", "")).strip()
            entity_id = payload.get("entity_id") or ""
            symbol = payload.get("symbol") or ""
            if not message:
                self.send_json({"reply": "问题不能为空。"}, status=400)
                return
            reply = call_remote_ai(message, entity_id, symbol) or local_answer(message, entity_id, symbol)
            self.send_json({"reply": reply})
        except Exception as exc:
            self.send_json({"reply": f"分析失败：{exc}"}, status=500)


if __name__ == "__main__":
    os.chdir(BASE_DIR)
    thread = threading.Thread(target=refresh_loop, daemon=True)
    thread.start()
    collect_thread = threading.Thread(target=daily_collect_loop, daemon=True)
    collect_thread.start()
    with ThreadedHTTPServer((HOST, PORT), ResearchHandler) as httpd:
        print(f"[{now_iso()}] open http://127.0.0.1:{PORT}")
        httpd.serve_forever()
