import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import Dict, Any, List
import logging
import datetime

from backend.config import load_config
from backend.market_service import MarketService
from backend.telegram_service import TelegramService

logger = logging.getLogger(__name__)

class SchedulerService:
    _scheduler: AsyncIOScheduler = None
    _execution_logs: List[Dict[str, Any]] = []

    @classmethod
    def get_scheduler(cls) -> AsyncIOScheduler:
        if cls._scheduler is None:
            cls._scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
        return cls._scheduler

    @classmethod
    def get_logs(cls) -> List[Dict[str, Any]]:
        return cls._execution_logs[-50:]  # 最近 50 条日志

    @classmethod
    def add_log(cls, schedule_id: str, schedule_name: str, status: str, detail: str):
        cls._execution_logs.append({
            "schedule_id": schedule_id,
            "schedule_name": schedule_name,
            "status": status,
            "detail": detail,
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    @classmethod
    async def trigger_schedule_now(cls, schedule_id: str) -> Dict[str, Any]:
        """立即手动触发一次定时任务 (测试/立刻播报)"""
        cfg = load_config()
        schedules = cfg.get("schedules", [])
        sched = next((s for s in schedules if s["id"] == schedule_id), None)
        if not sched:
            return {"success": False, "error": f"未找到定时任务: {schedule_id}"}
        
        return await cls._execute_task(sched)

    @classmethod
    async def _execute_task(cls, sched: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个市场任务的抓取与投递"""
        cfg = load_config()
        sched_id = sched["id"]
        sched_name = sched.get("name", sched_id)
        market_type = sched.get("market_type", "gold")
        target_topic_id = sched.get("target_topic_id")

        # 1. 获取目标 Topic 详情
        topics = cfg.get("topics", [])
        topic = next((t for t in topics if t["id"] == target_topic_id), None)
        thread_id = topic.get("thread_id") if topic else None

        # 2. 生成纯文本金融行情速报 (No image, pure clean text)
        try:
            if market_type == "gold":
                res = await MarketService.get_gold_market_data()
            elif market_type == "asia_stocks" or market_type == "us_stocks":
                res = await MarketService.get_global_stocks_data()
            else:
                res = await MarketService.get_market_intelligence_data()
            
            msg_text = res["telegram_message"]
        except Exception as e:
            err = f"获取市场行情失败: {e}"
            cls.add_log(sched_id, sched_name, "failed", err)
            return {"success": False, "error": err}

        # 3. 检查是否开启自动发送到 Telegram
        token = cfg.get("telegram", {}).get("bot_token")
        chat_id = cfg.get("telegram", {}).get("chat_id")

        if not sched.get("auto_send", True):
            cls.add_log(sched_id, sched_name, "generated_only", "已生成简报 (未开启自动发送)")
            return {"success": True, "message": "已生成简报草稿", "text": msg_text}

        if not token or not chat_id:
            msg = "Telegram Bot Token 或 Chat ID 尚未配置，仅生成行情未发送"
            cls.add_log(sched_id, sched_name, "warning", msg)
            return {"success": True, "warning": msg, "text": msg_text}

        # 4. 推送到对应群组话题 (纯文本直接推送)
        send_res = await TelegramService.send_message(
            token=token,
            chat_id=chat_id,
            text=msg_text,
            thread_id=thread_id,
            parse_mode="HTML"
        )

        if send_res.get("success"):
            detail = f"成功投递至 {topic['name'] if topic else '群组'} (Thread ID: {thread_id})"
            cls.add_log(sched_id, sched_name, "success", detail)
            return {"success": True, "detail": detail, "text": msg_text}
        else:
            detail = f"推送失败: {send_res.get('error')}"
            cls.add_log(sched_id, sched_name, "failed", detail)
            return {"success": False, "error": detail, "text": msg_text}

    @classmethod
    def reload_schedules(cls):
        """重新加载并启动所有启用的定时任务"""
        scheduler = cls.get_scheduler()
        scheduler.remove_all_jobs()

        cfg = load_config()
        schedules = cfg.get("schedules", [])

        for s in schedules:
            if not s.get("enabled", False):
                continue
            
            cron_expr = s.get("cron", "0 16 * * 1-5")
            try:
                parts = cron_expr.strip().split()
                if len(parts) == 5:
                    minute, hour, day, month, day_of_week = parts
                    trigger = CronTrigger(
                        minute=minute,
                        hour=hour,
                        day=day,
                        month=month,
                        day_of_week=day_of_week,
                        timezone="Asia/Shanghai"
                    )
                    scheduler.add_job(
                        cls._execute_task,
                        trigger=trigger,
                        args=[s],
                        id=s["id"],
                        name=s.get("name", s["id"]),
                        replace_existing=True
                    )
                    logger.info(f"已装载定时任务: {s.get('name')} -> {cron_expr}")
            except Exception as e:
                logger.error(f"解析任务 cron 失败 ({s.get('id')}): {e}")

        if not scheduler.running:
            scheduler.start()
            logger.info("APScheduler 服务已启动")
