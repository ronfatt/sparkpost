import os
import shutil
import asyncio
import base64
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
    update_schedules,
    update_twitter_settings
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
    image_filename: Optional[str] = None
    image_base64: Optional[str] = None

class SendSingleItemModel(BaseModel):
    topic_id: str
    thread_id: Optional[int] = None
    text: str
    image_filename: Optional[str] = None
    image_base64: Optional[str] = None

class SendBroadcastRequestModel(BaseModel):
    items: List[SendBroadcastItem]
    image_filename: Optional[str] = None
    image_base64: Optional[str] = None

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

@app.post("/api/broadcast/send_single")
async def send_single_broadcast(payload: SendSingleItemModel):
    """向单个话题发送消息/带图消息 (直传 Base64，抗 Vercel 无状态与超时)"""
    cfg = load_config()
    token = cfg.get("telegram", {}).get("bot_token")
    chat_id = cfg.get("telegram", {}).get("chat_id")

    if not token or not chat_id:
        raise HTTPException(status_code=400, detail="请先配置 Telegram Bot Token 和 群组 Chat ID")

    # 1. 优先从 Base64 解析图片
    item_img_bytes = None
    filename = payload.image_filename or "image.jpg"
    if payload.image_base64:
        try:
            b64_str = payload.image_base64
            if "," in b64_str:
                b64_str = b64_str.split(",", 1)[1]
            item_img_bytes = base64.b64decode(b64_str)
        except Exception as e:
            logger.warning(f"Base64 解码异常: {e}")

    # 2. 回退本地文件
    if not item_img_bytes and payload.image_filename:
        img_path = os.path.join(UPLOAD_DIR, payload.image_filename)
        if os.path.exists(img_path):
            with open(img_path, "rb") as f:
                item_img_bytes = f.read()

    th_id = payload.thread_id
    if item_img_bytes:
        if len(payload.text) <= 1024:
            res = await TelegramService.send_photo(
                token=token,
                chat_id=chat_id,
                photo_bytes=item_img_bytes,
                filename=filename,
                caption=payload.text,
                thread_id=th_id
            )
        else:
            await TelegramService.send_photo(
                token=token,
                chat_id=chat_id,
                photo_bytes=item_img_bytes,
                filename=filename,
                caption=None,
                thread_id=th_id
            )
            res = await TelegramService.send_message(
                token=token,
                chat_id=chat_id,
                text=payload.text,
                thread_id=th_id
            )
    else:
        res = await TelegramService.send_message(
            token=token,
            chat_id=chat_id,
            text=payload.text,
            thread_id=th_id
        )

    return {
        "success": res.get("success", False),
        "topic_id": payload.topic_id,
        "thread_id": th_id,
        "error": res.get("error") or ("Telegram 发送未成功，请检查 Bot 是否在该群组且拥有管理员权限" if not res.get("success") else None)
    }

@app.post("/api/broadcast/send")
async def send_broadcast(payload: SendBroadcastRequestModel):
    """一键向勾选的话题批量发送已翻译的消息，支持每个国家话题专属配图与防限流控制"""
    cfg = load_config()
    token = cfg.get("telegram", {}).get("bot_token")
    chat_id = cfg.get("telegram", {}).get("chat_id")

    if not token or not chat_id:
        raise HTTPException(status_code=400, detail="请先配置 Telegram Bot Token 和 群组 Chat ID")

    send_results = []
    
    # 平滑顺序分发，避免并发冲击触发 Telegram 429 限制
    for item in payload.items:
        th_id = item.thread_id
        
        # 1. 优先读取 Base64
        item_img_bytes = None
        item_img_name = item.image_filename or payload.image_filename
        target_b64 = item.image_base64 or payload.image_base64
        if target_b64:
            try:
                b64_str = target_b64
                if "," in b64_str:
                    b64_str = b64_str.split(",", 1)[1]
                item_img_bytes = base64.b64decode(b64_str)
            except Exception:
                pass
        
        # 2. 回退本地文件
        if not item_img_bytes and item_img_name:
            img_path = os.path.join(UPLOAD_DIR, item_img_name)
            if os.path.exists(img_path):
                with open(img_path, "rb") as f:
                    item_img_bytes = f.read()

        if item_img_bytes:
            # Telegram 规定 photo caption 最大为 1024 字符
            if len(item.text) <= 1024:
                res = await TelegramService.send_photo(
                    token=token,
                    chat_id=chat_id,
                    photo_bytes=item_img_bytes,
                    filename=item_img_name or "image.jpg",
                    caption=item.text,
                    thread_id=th_id
                )
            else:
                # 文本超过 1024 字符时，先发图再发长文案
                await TelegramService.send_photo(
                    token=token,
                    chat_id=chat_id,
                    photo_bytes=item_img_bytes,
                    filename=item_img_name or "image.jpg",
                    caption=None,
                    thread_id=th_id
                )
                res = await TelegramService.send_message(
                    token=token,
                    chat_id=chat_id,
                    text=item.text,
                    thread_id=th_id
                )
        else:
            res = await TelegramService.send_message(
                token=token,
                chat_id=chat_id,
                text=item.text,
                thread_id=th_id
            )

        print(f"DEBUG RES IN BROADCAST: res={res}, item_img_bytes len={len(item_img_bytes) if item_img_bytes else 0}")
        send_results.append({
            "topic_id": item.topic_id,
            "thread_id": th_id,
            "success": res.get("success", False),
            "error": res.get("error") or ("Telegram 发送未成功，请检查 Bot 是否在该群组且拥有管理员权限" if not res.get("success") else "")
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

# ================= SPARK ONE 核心卖点与公司优势宣传接口 =================
from backend.spark_pitch_service import SparkPitchService

class PitchSendModel(BaseModel):
    pitch_id: Optional[str] = None
    target_topic_id: Optional[str] = "general_chat"
    custom_text: Optional[str] = None

@app.get("/api/pitch/templates")
def get_pitch_templates():
    """获取所有官方卖点宣传文案列表"""
    return {"success": True, "templates": SparkPitchService.get_all_pitches()}

@app.post("/api/pitch/send")
async def send_pitch_content(payload: PitchSendModel):
    """一键向指定话题（默认 General Topic）发布公司核心卖点宣传"""
    cfg = load_config()
    token = cfg.get("telegram", {}).get("bot_token")
    chat_id = cfg.get("telegram", {}).get("chat_id")

    if not token or not chat_id:
        raise HTTPException(status_code=400, detail="请先配置 Telegram Bot Token 和 群组 Chat ID")

    topics = cfg.get("topics", [])
    target_topic = next((t for t in topics if t["id"] == (payload.target_topic_id or "general_chat")), None)
    thread_id = target_topic.get("thread_id") if target_topic else None

    if payload.custom_text:
        text = payload.custom_text
        title = "自定义宣传文案"
    else:
        p = SparkPitchService.get_pitch_by_id(payload.pitch_id) if payload.pitch_id else SparkPitchService.get_next_pitch_post()
        text = p["text"]
        title = p["title"]

    res = await TelegramService.send_message(
        token=token,
        chat_id=chat_id,
        text=text,
        thread_id=thread_id,
        parse_mode="HTML"
    )
    res["pitch_title"] = title
    return res

# ================= 定时任务接口 =================

@app.post("/api/scheduler/trigger/{schedule_id}")
async def trigger_schedule_now(schedule_id: str):
    """立即执行一次指定的定时任务"""
    return await SchedulerService.trigger_schedule_now(schedule_id)

@app.get("/api/scheduler/logs")
def get_scheduler_logs():
    """获取任务执行历史日志"""
    return SchedulerService.get_logs()

# ================= 7天多语言广播排期部署接口 =================
from backend.campaign_service import CampaignService

class TranslateDayRequestModel(BaseModel):
    day_index: int
    text: Optional[str] = None
    target_topic_ids: Optional[List[str]] = None

class ResetCampaignRequestModel(BaseModel):
    start_date: Optional[str] = None
    daily_time: Optional[str] = "10:00"

@app.get("/api/campaign/7days")
def get_campaign_7days():
    """获取当前 7 天广播排期配置与卡片状态"""
    return CampaignService.get_campaign()

@app.post("/api/campaign/7days")
def save_campaign_7days(payload: Dict[str, Any]):
    """保存并部署 7 天广播排期"""
    return {"success": True, "campaign": CampaignService.save_campaign(payload)}

@app.post("/api/campaign/7days/reset")
def reset_campaign_7days(payload: ResetCampaignRequestModel):
    """一键重置/生成 7 天标准推荐运营排期文案"""
    days = CampaignService.get_default_days(start_date_str=payload.start_date, default_time=payload.daily_time or "10:00")
    campaign = {
        "enabled": True,
        "daily_time": payload.daily_time or "10:00",
        "start_date": days[0]["send_date"],
        "days": days
    }
    return {"success": True, "campaign": CampaignService.save_campaign(campaign)}

@app.post("/api/campaign/7days/translate_day")
async def translate_campaign_day(payload: TranslateDayRequestModel):
    """为某一天并发翻译 11 国卡片"""
    cards = await CampaignService.translate_day_content(
        day_index=payload.day_index,
        custom_text=payload.text,
        target_topic_ids=payload.target_topic_ids
    )
    return {"success": True, "cards": cards, "campaign": CampaignService.get_campaign()}

@app.post("/api/campaign/7days/translate_all")
async def translate_all_campaign_days():
    """一键为全部 7 天生成多语言翻译卡片"""
    res = await CampaignService.translate_all_days()
    return res

@app.post("/api/campaign/7days/trigger/{day_index}")
async def trigger_campaign_day_now(day_index: int):
    """立即测试/手动执行指定某一天的 11 国广播投放"""
    return await CampaignService.execute_campaign_day(day_index, manual_trigger=True)

@app.get("/api/campaign/7days/check")
async def check_campaign_due_cron():
    """到期排期检测 (支持外部 Cron / Vercel Cron 心跳触发)"""
    results = await CampaignService.check_and_execute_due_days()
    return {"success": True, "executed_count": len(results), "results": results}

# ================= Twitter / X (x.com) 运营与自动发文接口 =================
from backend.twitter_service import TwitterService

class TwitterConfigModel(BaseModel):
    api_key: str
    api_secret: str
    access_token: str
    access_token_secret: str
    bearer_token: Optional[str] = ""
    enabled: bool = True

class TwitterVerifyModel(BaseModel):
    api_key: str
    api_secret: str
    access_token: str
    access_token_secret: str

class TweetPostModel(BaseModel):
    text: str
    image_filename: Optional[str] = None
    image_base64: Optional[str] = None

class TwitterScheduleModel(BaseModel):
    title: str
    text: str
    image_filename: Optional[str] = None
    image_base64: Optional[str] = None
    scheduled_date: str
    scheduled_time: str
    repeat: Optional[str] = "none"
    enabled: Optional[bool] = True

@app.get("/api/twitter/config")
def get_twitter_config():
    """获取当前推特绑定配置与状态"""
    cfg = load_config()
    tw = cfg.get("twitter", {})
    return {
        "success": True,
        "config": {
            "api_key": tw.get("api_key", ""),
            "api_secret": tw.get("api_secret", ""),
            "access_token": tw.get("access_token", ""),
            "access_token_secret": tw.get("access_token_secret", ""),
            "bearer_token": tw.get("bearer_token", ""),
            "enabled": tw.get("enabled", False),
            "account_info": tw.get("account_info", {})
        }
    }

@app.post("/api/twitter/config")
def save_twitter_config(payload: TwitterConfigModel):
    """保存推特配置并重启调度器"""
    cfg = update_twitter_settings(
        api_key=payload.api_key,
        api_secret=payload.api_secret,
        access_token=payload.access_token,
        access_token_secret=payload.access_token_secret,
        bearer_token=payload.bearer_token or "",
        enabled=payload.enabled
    )
    SchedulerService.reload_schedules()
    return {"success": True, "config": cfg.get("twitter", {})}

@app.post("/api/twitter/verify")
def verify_twitter_connection(payload: TwitterVerifyModel):
    """在线校验推特 API 凭证并获取当前推特账号信息"""
    return TwitterService.verify_credentials(
        api_key=payload.api_key,
        api_secret=payload.api_secret,
        access_token=payload.access_token,
        access_token_secret=payload.access_token_secret
    )

@app.post("/api/twitter/tweet")
def post_tweet_now(payload: TweetPostModel):
    """即时发布推文到 Twitter/X"""
    return TwitterService.post_tweet(
        text=payload.text,
        image_path=payload.image_filename,
        image_base64=payload.image_base64
    )

@app.get("/api/twitter/schedules")
def get_twitter_schedules():
    """获取所有已制定的推特自动发文排期"""
    return {"success": True, "schedules": TwitterService.load_schedules()}

@app.post("/api/twitter/schedules")
def add_twitter_schedule(payload: TwitterScheduleModel):
    """新增一条推特定时排期"""
    item = TwitterService.add_schedule(payload.model_dump())
    return {"success": True, "schedule": item}

@app.put("/api/twitter/schedules/{schedule_id}")
def update_twitter_schedule(schedule_id: str, payload: Dict[str, Any]):
    """更新一条推特定时排期"""
    item = TwitterService.update_schedule(schedule_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="未找到该推特排期任务")
    return {"success": True, "schedule": item}

@app.delete("/api/twitter/schedules/{schedule_id}")
def delete_twitter_schedule(schedule_id: str):
    """删除一条推特定时排期"""
    success = TwitterService.delete_schedule(schedule_id)
    return {"success": success}

@app.post("/api/twitter/schedules/{schedule_id}/trigger")
def trigger_twitter_schedule(schedule_id: str):
    """立即执行指定的推特排期任务"""
    return TwitterService.trigger_schedule_now(schedule_id)

@app.get("/api/twitter/templates")
def get_twitter_templates():
    """获取推特精选高转化文案模版"""
    return {"success": True, "templates": TwitterService.get_templates()}

@app.get("/api/twitter/check")
def check_twitter_due_cron():
    """推特到期排期检测 (支持外部 Cron / Vercel Cron 心跳)"""
    results = TwitterService.check_and_execute_due_tweets()
    return {"success": True, "executed_count": len(results), "results": results}

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
