import os
import json
import asyncio
import base64
import datetime
import logging
from typing import Dict, Any, List, Optional

from backend.config import load_config, save_config
from backend.translation_service import TranslationService
from backend.telegram_service import TelegramService

logger = logging.getLogger(__name__)

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))

class CampaignService:
    """
    7天自动化广播排期与投放管理服务
    支持：
    1. 预先部署 7 天内容规划与每日定时触发 (可按天定制时间，默认每日 10:00)
    2. 多语言并发自动翻译 (提前生成或定时自动翻译 11 国卡片)
    3. 支持每日前期带图/Base64配图部署
    4. 支持立即试发、排期倒计时、状态追踪与自动重发
    """

    DEFAULT_TEMPLATES = [
        {
            "day": 1,
            "title": "Day 1 🌟 SparkOne 全球生态启航 • 新人起步指南",
            "text": (
                "🌟 **SPARK ONE • 全球生态启航 & 新人起步指南**\n\n"
                "亲爱的社区成员，欢迎加入 **SPARK ONE** 全球官方社群！\n\n"
                "📌 **社群核心指引：**\n"
                "• 🌍 **11国语言国家区**：请进入对应语言话题，与全球伙伴母语交流\n"
                "• 🥇 **黄金与 RWA 金融区**：实时追踪链上代币化黄金与大宗行情\n"
                "• 🤖 **SPARK AI 投研区**：每天获取独家彭博级 AI 量化行情脉搏\n\n"
                "🛡️ **安全第一原则**：官方管理员绝不会私聊索要私钥或密码！\n\n"
                "#SparkOne #Welcome #GlobalCommunity #Web3"
            )
        },
        {
            "day": 2,
            "title": "Day 2 🪙 区块链黄金 (RWA) 实物储备与透明度解读",
            "text": (
                "🪙 **SPARK ONE • 区块链代币化黄金 (RWA) 机制深度解析**\n\n"
                "为什么我们专注代币化黄金？\n\n"
                "• 🏛️ **100% 实物黄金托底**：每一枚 PAXG / XAUT 均对应伦敦金库真实金条\n"
                "• ⚡ **链上极速流转**：彻底打破传统实物金保管难、交割慢、门槛高的壁垒\n"
                "• 🛡️ **抗通胀与避险锚点**：在全球宏观波动中为数字资产组合提供坚实防线\n\n"
                "让实体价值在区块链上自由流动，这就是 RWA 的力量！\n\n"
                "#Gold #RWA #PAXG #XAUT #AssetAllocation"
            )
        },
        {
            "day": 3,
            "title": "Day 3 🤖 SPARK AI 5大投研引擎运行原理 • 让数据驱动交易",
            "text": (
                "🧠 **HOW SPARK AI THINKS • 认识 5 大核心量化引擎**\n\n"
                "SPARK AI 不是简单的机器人，而是一整套多维量化系统：\n\n"
                "• 🟡 **AURORA**：宏观流动性与黄金储备监测引擎\n"
                "• 📈 **TITAN**：跨资产多周期动能与趋势识别引擎\n"
                "• 🛡️ **ORION**：中央免疫系统，执行严格左尾回撤风控\n"
                "• ⚡ **PHOENIX**：策略执行效率与参数动态优化引擎\n"
                "• 🌐 **ATLAS**：全景资产配置与夏普比率平衡引擎\n\n"
                "AI 不靠情绪交易，只依循数据、概率与风控准则。\n\n"
                "#SparkAI #QuantEngines #FinTech #AlgorithmicTrading"
            )
        },
        {
            "day": 4,
            "title": "Day 4 🎁 社区阶段性成长激励与福利任务全面开启",
            "text": (
                "🎁 **SPARK ONE • 社区成长激励与专属福利任务**\n\n"
                "为了回馈全球活跃成员，本周专属任务正式解锁！\n\n"
                "🎯 **任务清单：**\n"
                "1️⃣ 每日在所属国家话题完成互动交流\n"
                "2️⃣ 邀请志同道合的行业伙伴加入全球大家庭\n"
                "3️⃣ 参与每周 SPARK AI 市场观点投票与模拟研讨\n\n"
                "🏆 积极贡献者将享有核心权益加成与优先体验名额！\n\n"
                "#Rewards #Missions #CommunityFirst #SparkOne"
            )
        },
        {
            "day": 5,
            "title": "Day 5 📊 跨资产深度宏观研报 • 黄金、美股与加密流动性周评",
            "text": (
                "📊 **SPARK ONE • 跨资产宏观研报与流动性深度周评**\n\n"
                "本周全球核心资产脉搏梳理：\n\n"
                "• 💵 **美元与美债收益率**：宏观降息预期博弈持续，利率敏感资产高位震荡\n"
                "• 🥇 **黄金与避险大宗**：央行持续净购金与去美元化需求支撑现货金稳步上扬\n"
                "• 💻 **科技巨头与芯片**：AI 基础设施资本支出强劲，龙头股展现高韧性\n"
                "• ⚡ **加密市场**：主要 Layer-1 活跃地址与链上结算量保持健康扩张\n\n"
                "多维数据归因，助你穿透市场噪音，看清大资金流向！\n\n"
                "#MacroIntelligence #GlobalMarkets #Liquidity #WeeklyWrap"
            )
        },
        {
            "day": 6,
            "title": "Day 6 🎓 AI Quant 量化微课堂 • 建立纪律与克服情绪化交易",
            "text": (
                "🎓 **SPARK AI KNOWLEDGE • 为什么业余者看胜率，专家看回撤？**\n\n"
                "在交易世界中，摧毁本金的往往不是缺乏机会，而是没有风控纪律。\n\n"
                "📉 **回撤数学事实：**\n"
                "• 亏损 10% 需要上涨 11.1% 才能回本\n"
                "• 亏损 50% 需要上涨 **100%** 才能回本\n"
                "• 亏损 80% 需要上涨 **400%** 才能回本\n\n"
                "🛡️ **量化第一法则**：本金安全永远优先于追逐利润。\n"
                "跟随算法，制定预案，严格止损，让时间成为复利的朋友。\n\n"
                "#QuantAcademy #RiskFirst #Discipline #InvestmentMindset"
            )
        },
        {
            "day": 7,
            "title": "Day 7 🚀 未来一周重要宏观事件预警 & 社区周度互动预告",
            "text": (
                "🚀 **SPARK ONE • 未来一周全球宏观风险日历 & 社区互动**\n\n"
                "下周关键事件前瞻，请提前做好仓位管理与风险防范：\n\n"
                "📅 **宏观关键日程：**\n"
                "• 周二：欧美非制造业 PMI 数据公布\n"
                "• 周四：美国初请失业金人数 & 美联储理事发言\n"
                "• 周五：非农就业与核心 CPI 关键通胀指标披露\n\n"
                "🎙️ **周日社区 AMA 线上互动**：我们将深度探讨 AI 量化策略最新优化进展，不见不散！\n\n"
                "#WeekAhead #MacroCalendar #SparkAMA #NextWeek"
            )
        }
    ]

    @classmethod
    def get_default_days(cls, start_date_str: Optional[str] = None, default_time: str = "10:00") -> List[Dict[str, Any]]:
        """生成标准 7 天排期默认结构"""
        base_date = datetime.datetime.now()
        if start_date_str:
            try:
                base_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
            except Exception:
                pass

        days = []
        for item in cls.DEFAULT_TEMPLATES:
            idx = item["day"]
            target_date = (base_date + datetime.timedelta(days=idx - 1)).strftime("%Y-%m-%d")
            days.append({
                "day_index": idx,
                "title": item["title"],
                "send_date": target_date,
                "send_time": default_time,
                "enabled": True,
                "text": item["text"],
                "image_filename": None,
                "image_base64": None,
                "status": "pending",  # pending | sending | success | failed | paused
                "last_executed": None,
                "execution_result": None,
                "cards": []
            })
        return days

    @classmethod
    def get_campaign(cls) -> Dict[str, Any]:
        """获取当前配置的 7 天广播排期"""
        cfg = load_config()
        campaign = cfg.get("campaign_7days")
        if not campaign or not campaign.get("days"):
            default_days = cls.get_default_days()
            campaign = {
                "enabled": True,
                "daily_time": "10:00",
                "start_date": default_days[0]["send_date"],
                "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "days": default_days
            }
            cfg["campaign_7days"] = campaign
            save_config(cfg)
        return campaign

    @classmethod
    def save_campaign(cls, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """保存 7 天排期并重新加载调度器"""
        cfg = load_config()
        campaign_data["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cfg["campaign_7days"] = campaign_data
        save_config(cfg)

        # 触发调度器热重载
        try:
            from backend.scheduler_service import SchedulerService
            SchedulerService.reload_schedules()
        except Exception as e:
            logger.warning(f"重新加载调度器异常: {e}")

        return campaign_data

    @classmethod
    async def translate_day_content(
        cls,
        day_index: int,
        custom_text: Optional[str] = None,
        target_topic_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """为指定的某一天并发翻译 11 国卡片"""
        campaign = cls.get_campaign()
        days = campaign.get("days", [])
        day = next((d for d in days if d["day_index"] == day_index), None)
        if not day:
            raise ValueError(f"未找到 Day {day_index}")

        text = (custom_text or day.get("text", "")).strip()
        if not text:
            raise ValueError("内容不能为空")

        cfg = load_config()
        topics = cfg.get("topics", [])
        if target_topic_ids:
            topics = [t for t in topics if t["id"] in target_topic_ids]

        trans_cfg = cfg.get("translation", {})
        results = await TranslationService.translate_batch(
            text=text,
            topics=topics,
            engine=trans_cfg.get("engine", "built-in"),
            api_key=trans_cfg.get("api_key", ""),
            model=trans_cfg.get("model", "gemini-1.5-flash")
        )

        day_img = day.get("image_filename")
        day_b64 = day.get("image_base64")

        # 映射生成卡片结构
        cards = []
        for r in results:
            cards.append({
                "topic_id": r["topic_id"],
                "topic_name": r["topic_name"],
                "target_lang": r["target_lang"],
                "target_lang_name": r["target_lang_name"],
                "thread_id": r.get("thread_id"),
                "translated_text": r["translated_text"],
                "image_filename": day_img,
                "image_base64": day_b64,
                "send_status": "ready",
                "error_msg": ""
            })

        # 回写到 campaign
        day["text"] = text
        day["cards"] = cards
        cls.save_campaign(campaign)
        return cards

    @classmethod
    async def translate_all_days(cls) -> Dict[str, Any]:
        """一键并发为全部 7 天生成多语言翻译卡片"""
        campaign = cls.get_campaign()
        days = campaign.get("days", [])
        results = {}
        for day in days:
            idx = day["day_index"]
            try:
                cards = await cls.translate_day_content(idx)
                results[f"day_{idx}"] = {"success": True, "count": len(cards)}
            except Exception as e:
                results[f"day_{idx}"] = {"success": False, "error": str(e)}
        return {"success": True, "results": results, "campaign": cls.get_campaign()}

    @classmethod
    async def execute_campaign_day(cls, day_index: int, manual_trigger: bool = False) -> Dict[str, Any]:
        """
        执行指定某一天的 11 国语言广播投放
        平滑分发给每个话题，规避 Telegram 限流
        """
        campaign = cls.get_campaign()
        days = campaign.get("days", [])
        day = next((d for d in days if d["day_index"] == day_index), None)
        if not day:
            return {"success": False, "error": f"未找到 Day {day_index}"}

        cfg = load_config()
        token = cfg.get("telegram", {}).get("bot_token")
        chat_id = cfg.get("telegram", {}).get("chat_id")

        if not token or not chat_id:
            return {"success": False, "error": "请先配置 Telegram Bot Token 和群组 Chat ID"}

        # 若卡片尚未翻译，则现场快速并发翻译
        cards = day.get("cards", [])
        if not cards or len(cards) == 0:
            logger.info(f"Day {day_index} 卡片未预先翻译，现场自动生成...")
            try:
                cards = await cls.translate_day_content(day_index)
            except Exception as e:
                return {"success": False, "error": f"现场自动翻译失败: {e}"}

        day["status"] = "sending"
        cls.save_campaign(campaign)

        success_count = 0
        fail_count = 0
        dispatch_logs = []

        day_img_name = day.get("image_filename")
        day_b64 = day.get("image_base64")

        for card in cards:
            th_id = card.get("thread_id")
            card_text = card.get("translated_text", "")
            target_name = card.get("topic_name", card.get("topic_id"))

            # 解析图片
            target_img_bytes = None
            target_img_name = card.get("image_filename") or day_img_name
            target_b64 = card.get("image_base64") or day_b64

            if target_b64:
                try:
                    b64_str = target_b64
                    if "," in b64_str:
                        b64_str = b64_str.split(",", 1)[1]
                    target_img_bytes = base64.b64decode(b64_str)
                except Exception:
                    pass

            if not target_img_bytes and target_img_name:
                img_path = os.path.join(UPLOAD_DIR, target_img_name)
                if os.path.exists(img_path):
                    try:
                        with open(img_path, "rb") as f:
                            target_img_bytes = f.read()
                    except Exception:
                        pass

            try:
                if target_img_bytes:
                    if len(card_text) <= 1024:
                        res = await TelegramService.send_photo(
                            token=token,
                            chat_id=chat_id,
                            photo_bytes=target_img_bytes,
                            filename=target_img_name or "image.jpg",
                            caption=card_text,
                            thread_id=th_id
                        )
                    else:
                        await TelegramService.send_photo(
                            token=token,
                            chat_id=chat_id,
                            photo_bytes=target_img_bytes,
                            filename=target_img_name or "image.jpg",
                            caption=None,
                            thread_id=th_id
                        )
                        res = await TelegramService.send_message(
                            token=token,
                            chat_id=chat_id,
                            text=card_text,
                            thread_id=th_id
                        )
                else:
                    res = await TelegramService.send_message(
                        token=token,
                        chat_id=chat_id,
                        text=card_text,
                        thread_id=th_id
                    )

                if res.get("success"):
                    card["send_status"] = "success"
                    card["error_msg"] = ""
                    success_count += 1
                    dispatch_logs.append(f"✅ {target_name}: 成功 (ID: {res.get('message_id')})")
                else:
                    card["send_status"] = "error"
                    card["error_msg"] = res.get("error", "未知错误")
                    fail_count += 1
                    dispatch_logs.append(f"❌ {target_name}: 失败 ({res.get('error')})")
            except Exception as e:
                card["send_status"] = "error"
                card["error_msg"] = str(e)
                fail_count += 1
                dispatch_logs.append(f"❌ {target_name}: 异常 ({e})")

            # 停顿 250ms 平滑发送
            await asyncio.sleep(0.25)

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        day["status"] = "success" if fail_count == 0 else ("partial" if success_count > 0 else "failed")
        day["last_executed"] = now_str
        day["execution_result"] = {
            "success_count": success_count,
            "fail_count": fail_count,
            "total": len(cards),
            "executed_at": now_str,
            "manual": manual_trigger,
            "logs": dispatch_logs
        }

        cls.save_campaign(campaign)

        # 写入调度器全局日志
        try:
            from backend.scheduler_service import SchedulerService
            status_tag = "success" if fail_count == 0 else "warning"
            SchedulerService.add_log(
                schedule_id=f"campaign_day_{day_index}",
                schedule_name=f"7天广播排期: {day['title']}",
                status=status_tag,
                detail=f"成功: {success_count} 个话题，失败: {fail_count} 个话题"
            )
        except Exception:
            pass

        return {
            "success": success_count > 0,
            "day_index": day_index,
            "success_count": success_count,
            "fail_count": fail_count,
            "executed_at": now_str,
            "logs": dispatch_logs
        }

    @classmethod
    async def check_and_execute_due_days(cls) -> List[Dict[str, Any]]:
        """
        心跳轮询：检查是否有到期尚未执行的排期任务并执行
        支持云端唤醒与本地后台高容错 (服务器重启或休眠苏醒后自动补发)
        """
        campaign = cls.get_campaign()
        if not campaign.get("enabled", True):
            return []

        days = campaign.get("days", [])
        now = datetime.datetime.now()
        now_dt_str = now.strftime("%Y-%m-%d %H:%M")

        results = []
        for day in days:
            if not day.get("enabled", True):
                continue
            if day.get("status") in ("success", "sending"):
                continue

            send_date = day.get("send_date", "").strip()
            send_time = day.get("send_time", "10:00").strip()
            if not send_date:
                continue

            try:
                scheduled_dt = datetime.datetime.strptime(f"{send_date} {send_time}", "%Y-%m-%d %H:%M")
                # 如果当前时间已到达或略超排期时间（且在 24 小时容差内）
                if now >= scheduled_dt and (now - scheduled_dt).total_seconds() < 86400:
                    logger.info(f"触发到期排期广播: Day {day['day_index']} ({send_date} {send_time})")
                    res = await cls.execute_campaign_day(day["day_index"], manual_trigger=False)
                    results.append(res)
            except Exception as e:
                logger.error(f"解析 Day {day.get('day_index')} 排期时间失败: {e}")

        return results
