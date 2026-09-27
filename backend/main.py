import os
import shutil
import asyncio
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import (
    load_config,
    save_config,
    update_telegram_settings,
    update_translation_settings,
    update_topics,
    update_schedules
)
from backend.telegram_service import TelegramService
from backend.translation_service import TranslationService
from backend.market_service import MarketService
from backend.scheduler_service import SchedulerService

app = FastAPI(title="SparkOne Telegram Multi-Topic Broadcast & Market Center")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

IS_VERCEL = os.environ.get("VERCEL") == "1" or os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None

if IS_VERCEL:
    UPLOAD_DIR = "/tmp/uploads"
else:
    UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))

STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "static"))
TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "templates"))

try:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
except Exception:
    pass

try:
    os.makedirs(STATIC_DIR, exist_ok=True)
except Exception:
    pass

try:
    if os.path.exists(STATIC_DIR):
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    if os.path.exists(UPLOAD_DIR):
        app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
except Exception:
    pass

@app.on_event("startup")
async def on_startup():
    # Vercel Serverless 下不启动常驻线程定时器，由 Vercel Cron Job 触发
    if not IS_VERCEL:
        try:
            SchedulerService.reload_schedules()
        except Exception:
            pass

# ================= 数据模型 =================
class TelegramConfigModel(BaseModel):
    bot_token: str
    chat_id: str

class TranslationConfigModel(BaseModel):
    engine: str
    api_key: str = ""
    model: str = ""

class TranslateRequestModel(BaseModel):
    text: str
    target_topic_ids: Optional[List[str]] = None

class SendBroadcastItem(BaseModel):
    topic_id: str
    thread_id: Optional[int] = None
    text: str

class SendBroadcastRequestModel(BaseModel):
    items: List[SendBroadcastItem]
    image_filename: Optional[str] = None

class MarketSendModel(BaseModel):
    topic_id: str
    thread_id: Optional[int] = None
    text: str

# ================= 接口路由 =================

@app.get("/api/config")
def get_current_config():
    """获取所有配置"""
    return load_config()

@app.post("/api/config/telegram")
async def save_telegram_config(payload: TelegramConfigModel):
    """保存并验证 Telegram Bot 设置"""
    bot_token = payload.bot_token.strip()
    chat_id = payload.chat_id.strip()
    
    # 验证 Bot 有效性
    verify_res = await TelegramService.verify_bot(bot_token) if bot_token else {"success": False, "error": "Token 为空"}
    
    update_telegram_settings(bot_token, chat_id)
    return {
        "success": True,
        "config": load_config(),
        "verification": verify_res
    }

@app.post("/api/config/translation")
def save_translation_config(payload: TranslationConfigModel):
    """保存翻译引擎设置"""
    update_translation_settings(payload.engine, payload.api_key, payload.model)
    return {"success": True, "config": load_config()}

@app.post("/api/config/topics")
def save_topics_config(payload: List[Dict[str, Any]]):
    """保存 Topics 列表及 Thread ID 绑定"""
    update_topics(payload)
    return {"success": True, "topics": payload}

@app.post("/api/config/schedules")
def save_schedules_config(payload: List[Dict[str, Any]]):
    """保存定时任务并重新载入调度器"""
    update_schedules(payload)
    SchedulerService.reload_schedules()
    return {"success": True, "schedules": payload}

@app.post("/api/telegram/detect")
async def detect_topics():
    """从 Telegram updates 自动探测群组 ID 与 Topic Thread IDs"""
    cfg = load_config()
    token = cfg.get("telegram", {}).get("bot_token")
    if not token:
        raise HTTPException(status_code=400, detail="请先在设置中保存 Bot Token")
    
    return await TelegramService.detect_topics_from_updates(token)

@app.post("/api/broadcast/translate")
async def translate_broadcast_content(payload: TranslateRequestModel):
    """一键将原文翻译成所有启用的国家语言"""
    cfg = load_config()
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="广播文本内容不能为空")

    topics = cfg.get("topics", [])
    if payload.target_topic_ids:
        topics = [t for t in topics if t["id"] in payload.target_topic_ids]

    trans_cfg = cfg.get("translation", {})
    engine = trans_cfg.get("engine", "built-in")
    api_key = trans_cfg.get("api_key", "")
    model = trans_cfg.get("model", "gemini-1.5-flash")

    results = await TranslationService.translate_batch(
        text=text,
        topics=topics,
        engine=engine,
        api_key=api_key,
        model=model
    )
    return {"success": True, "results": results}

@app.post("/api/upload_image")
async def upload_image(file: UploadFile = File(...)):
    """上传广播配图"""
    ext = os.path.splitext(file.filename)[1].lower() or ".jpg"
    filename = f"img_{int(asyncio.get_event_loop().time() * 1000)}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"success": True, "filename": filename, "url": f"/uploads/{filename}"}

from backend.card_generator import CardGenerator

# ... (数据模型保持不变) ...

@app.post("/api/broadcast/send")
async def send_broadcast(payload: SendBroadcastRequestModel):
    """一键向勾选的话题批量发送已翻译的消息，内置平滑排队与防限流控制"""
    cfg = load_config()
    token = cfg.get("telegram", {}).get("bot_token")
    chat_id = cfg.get("telegram", {}).get("chat_id")

    if not token or not chat_id:
        raise HTTPException(status_code=400, detail="请先配置 Telegram Bot Token 和 群组 Chat ID")

    image_bytes = None
    if payload.image_filename:
        img_path = os.path.join(UPLOAD_DIR, payload.image_filename)
        if os.path.exists(img_path):
            with open(img_path, "rb") as f:
                image_bytes = f.read()

    send_results = []
    
    # 平滑顺序分发，避免并发冲击触发 Telegram 429 限制
    for item in payload.items:
        th_id = item.thread_id
        if image_bytes:
            res = await TelegramService.send_photo(
                token=token,
                chat_id=chat_id,
                photo_bytes=image_bytes,
                filename=payload.image_filename or "image.jpg",
                caption=item.text,
                thread_id=th_id
            )
        else:
            res = await TelegramService.send_message(
                token=token,
                chat_id=chat_id,
                text=item.text,
                thread_id=th_id
            )
        send_results.append({
            "topic_id": item.topic_id,
            "thread_id": th_id,
            "success": res.get("success", False),
            "error": res.get("error")
        })
        # 平滑延迟 0.35 秒
        await asyncio.sleep(0.35)

    return {"success": True, "results": send_results}

# ================= 市场数据接口 (纯文本极简金融终端模式) =================

@app.get("/api/market/data/{market_type}")
async def get_market_data(market_type: str):
    """获取实时金融行情并返回 Telegram 格式纯文本"""
    if market_type == "gold":
        return await MarketService.get_gold_market_data()
    elif market_type in ["asia_stocks", "us_stocks", "global_stocks"]:
        return await MarketService.get_global_stocks_data()
    else:
        return await MarketService.get_market_intelligence_data()

class MarketSendModel(BaseModel):
    topic_id: str
    thread_id: Optional[int] = None
    text: str

@app.post("/api/market/send")
async def send_market_report(payload: MarketSendModel):
    """手动将编辑好的纯文本市场行情推送到指定话题"""
    cfg = load_config()
    token = cfg.get("telegram", {}).get("bot_token")
    chat_id = cfg.get("telegram", {}).get("chat_id")

    if not token or not chat_id:
        raise HTTPException(status_code=400, detail="请先配置 Telegram Bot Token 和 群组 Chat ID")

    return await TelegramService.send_message(
        token=token,
        chat_id=chat_id,
        text=payload.text,
        thread_id=payload.thread_id,
        parse_mode="HTML"
    )

from backend.spark_ai_service import SparkAIService

# ================= SPARK AI 官方投研中心接口 =================

class SparkAISendModel(BaseModel):
    text: str
    topic_id: str = "spark_ai"

@app.get("/api/spark_ai/generate/{content_type}")
async def generate_spark_ai_content(content_type: str, index: int = 0):
    """根据类型实时生成 SPARK AI 官方研究内容"""
    if content_type == "random":
        res = await SparkAIService.generate_random_hourly_post()
        return {"success": True, "title": res["title"], "text": res["text"], "pillar": res.get("pillar")}
    elif content_type == "daily":
        text = await SparkAIService.generate_daily_brief()
        title = "⚡ SPARK AI DAILY"
    elif content_type == "intelligence":
        text = await SparkAIService.generate_market_intelligence()
        title = "📊 AI MARKET INTELLIGENCE"
    elif content_type == "how_thinks":
        text = SparkAIService.generate_how_spark_ai_thinks(index)
        title = "🧠 HOW SPARK AI THINKS"
    elif content_type == "risk_alert":
        text = SparkAIService.generate_risk_alert()
        title = "🚨 SPARK AI RISK ALERT"
    elif content_type == "knowledge":
        text = SparkAIService.get_knowledge_item(index)
        title = f"🎓 SPARK AI KNOWLEDGE"
    else:
        text = SparkAIService.get_insight()
        title = "✨ SPARK AI INSIGHT"

    return {"success": True, "title": title, "text": text}

@app.get("/api/spark_ai/random")
async def get_random_spark_ai():
    """随机生成一条 SPARK AI 6大核心支柱内容"""
    res = await SparkAIService.generate_random_hourly_post()
    return {"success": True, "title": res["title"], "text": res["text"], "pillar": res.get("pillar")}


@app.post("/api/spark_ai/send")
async def send_spark_ai_content(payload: SparkAISendModel):
    """一键推送 SPARK AI 投研内容至 SPARK AI 话题"""
    cfg = load_config()
    token = cfg.get("telegram", {}).get("bot_token")
    chat_id = cfg.get("telegram", {}).get("chat_id")

    if not token or not chat_id:
        raise HTTPException(status_code=400, detail="请先配置 Telegram Bot Token 和 群组 Chat ID")

    topics = cfg.get("topics", [])
    spark_ai_topic = next((t for t in topics if t["id"] == "spark_ai"), None)
    thread_id = spark_ai_topic.get("thread_id") if spark_ai_topic else None

    return await TelegramService.send_message(
        token=token,
        chat_id=chat_id,
        text=payload.text,
        thread_id=thread_id,
        parse_mode="HTML"
    )

# ================= 定时任务接口 =================

@app.post("/api/scheduler/trigger/{schedule_id}")
async def trigger_schedule_now(schedule_id: str):
    """立即执行一次指定的定时任务"""
    return await SchedulerService.trigger_schedule_now(schedule_id)

@app.get("/api/scheduler/logs")
def get_scheduler_logs():
    """获取任务执行历史日志"""
    return SchedulerService.get_logs()

# ================= 页面首页 =================

@app.get("/", response_class=HTMLResponse)
def index_page():
    candidates = [
        os.path.join(TEMPLATES_DIR, "index.html"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "templates", "index.html")),
        os.path.abspath("frontend/templates/index.html"),
        "/var/task/frontend/templates/index.html"
    ]
    for p in candidates:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return f.read()
    return "<h1>SparkOne Telegram Web Dashboard is initializing...</h1>"
