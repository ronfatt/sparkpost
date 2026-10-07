import os
import re
import json
import base64
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import requests
from requests_oauthlib import OAuth1

from .config import load_config, save_config, update_twitter_settings
from .twitter_content_generator import TwitterContentGenerator

logger = logging.getLogger("twitter_service")

DATA_DIR = Path(__file__).parent.parent / "data"
UPLOADS_DIR = Path(__file__).parent.parent / "uploads"
SCHEDULES_FILE = DATA_DIR / "twitter_schedules.json"
TMP_SCHEDULES_FILE = Path("/tmp/twitter_schedules.json")

TWITTER_V2_TWEET_URL = "https://api.twitter.com/2/tweets"
TWITTER_V2_ME_URL = "https://api.twitter.com/2/users/me?user.fields=profile_image_url,description,public_metrics,verified"
TWITTER_V1_MEDIA_UPLOAD_URL = "https://upload.twitter.com/1.1/media/upload.json"

DEFAULT_TWEET_TEMPLATES = [
    {
        "id": "tw_tmpl_1",
        "title": "🪙 区块链黄金 RWA 实物背书推文",
        "category": "rwa",
        "text": "🪙 Physical Gold meets On-Chain Liquidity.\n\nEvery tokenized ounce of gold is 100% backed by LBMA-certified vaults. Protect your digital portfolio against inflation with instant 24/7 liquidity.\n\n🌐 Explore: https://sparkunioncapital.com/\n\n#Gold #RWA #PAXG #Crypto #Web3 #Tokenization"
    },
    {
        "id": "tw_tmpl_2",
        "title": "🤖 SPARK AI 彭博级量化投研早报",
        "category": "ai",
        "text": "🤖 SPARK AI Daily Market Pulse:\n\nOur 5 quantitative engines just completed global multi-asset volatility scans.\n\n• Gold: Consolidating near key structural support\n• BTC/ETH: Derivatives funding rates resetting\n• Macro: Eyes on Fed rate projections\n\nFull desk alpha inside the terminal 📊\n\n#SparkOne #AI #Quant #Bitcoin #Trading"
    },
    {
        "id": "tw_tmpl_3",
        "title": "🚀 社区生态起航与全球节点激励",
        "category": "community",
        "text": "🚀 SPARK ONE Global Ecosystem is expanding rapidly!\n\n11 multilingual national hubs are now live on Telegram. Join community missions, earn ecosystem points, and participate in node rewards.\n\n👉 Join official hubs: https://sparkunioncapital.com/\n\n#SparkOne #Airdrop #Community #DeFi #Web3"
    },
    {
        "id": "tw_tmpl_4",
        "title": "🚨 官方安全与防钓鱼最高警报",
        "category": "security",
        "text": "🚨 Official Security Notice:\n\nSparkOne admins will NEVER DM you first or ask for private keys/seed phrases. Always verify links via official portals.\n\nStay vigilant and protect your vault assets! 🛡️\n\n#Web3Security #CryptoSafety #AntiPhishing #SparkOne"
    }
]


class TwitterService:

    @staticmethod
    def _get_schedules_path() -> Path:
        if TMP_SCHEDULES_FILE.exists():
            return TMP_SCHEDULES_FILE
        if SCHEDULES_FILE.exists():
            return SCHEDULES_FILE
        return SCHEDULES_FILE

    @classmethod
    def get_auth(cls, config_override: Optional[Dict[str, Any]] = None) -> Optional[OAuth1]:
        cfg = config_override or load_config()
        tw = cfg.get("twitter", {})
        api_key = tw.get("api_key", "").strip()
        api_secret = tw.get("api_secret", "").strip()
        access_token = tw.get("access_token", "").strip()
        access_token_secret = tw.get("access_token_secret", "").strip()

        if not (api_key and api_secret and access_token and access_token_secret):
            return None

        return OAuth1(api_key, api_secret, access_token, access_token_secret)

    @classmethod
    def verify_credentials(cls, api_key: str, api_secret: str, access_token: str, access_token_secret: str) -> Dict[str, Any]:
        """验证推特 API 凭据并获取当前账户信息"""
        try:
            auth = OAuth1(api_key.strip(), api_secret.strip(), access_token.strip(), access_token_secret.strip())
            resp = requests.get(TWITTER_V2_ME_URL, auth=auth, timeout=12)
            
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                account_info = {
                    "id": data.get("id"),
                    "name": data.get("name"),
                    "username": data.get("username"),
                    "profile_image_url": data.get("profile_image_url"),
                    "description": data.get("description"),
                    "followers_count": data.get("public_metrics", {}).get("followers_count", 0),
                    "verified": data.get("verified", False)
                }
                # 自动保存验证成功的信息
                update_twitter_settings(
                    api_key=api_key,
                    api_secret=api_secret,
                    access_token=access_token,
                    access_token_secret=access_token_secret,
                    enabled=True,
                    account_info=account_info
                )
                return {"success": True, "user": account_info}
            
            error_data = {}
            try:
                error_data = resp.json()
            except Exception:
                pass

            err_msg = error_data.get("detail") or error_data.get("title") or resp.text
            if resp.status_code == 401:
                return {
                    "success": False,
                    "error": f"认证失败 (401 Unauthorized): 请检查 API Key, Secret 和 Access Tokens 是否正确填写。\n详情: {err_msg}"
                }
            elif resp.status_code == 403:
                return {
                    "success": False,
                    "error": f"权限不足 (403 Forbidden): 请确保在 Twitter Developer Portal 中该 App 的权限已设置为 'Read and Write'，且在修改权限后重新生成了 Access Token。\n详情: {err_msg}"
                }
            else:
                return {
                    "success": False,
                    "error": f"Twitter API 响应错误 ({resp.status_code}): {err_msg}"
                }

        except Exception as e:
            logger.error(f"Twitter 凭证验证异常: {e}")
            return {"success": False, "error": f"网络或系统异常: {str(e)}"}

    @classmethod
    def _extract_media_bytes(cls, image_path: Optional[str] = None, image_base64: Optional[str] = None) -> Optional[bytes]:
        """从路径或 Base64 提取图片原始二进制字节"""
        if image_base64:
            try:
                raw_b64 = image_base64
                if "," in raw_b64:
                    raw_b64 = raw_b64.split(",", 1)[1]
                return base64.b64decode(raw_b64)
            except Exception as e:
                logger.error(f"Base64 解码图片失败: {e}")

        if image_path:
            # 尝试绝对路径
            p = Path(image_path)
            if not p.is_absolute():
                p = UPLOADS_DIR / image_path
            if p.exists():
                try:
                    with open(p, "rb") as f:
                        return f.read()
                except Exception as e:
                    logger.error(f"读取图片文件失败: {e}")
        return None

    @classmethod
    def upload_media(cls, auth: OAuth1, image_bytes: bytes) -> Optional[str]:
        """上传图片到 Twitter 1.1 media upload 接口，返回 media_id"""
        try:
            files = {"media": image_bytes}
            resp = requests.post(TWITTER_V1_MEDIA_UPLOAD_URL, auth=auth, files=files, timeout=20)
            if resp.status_code in [200, 201, 202]:
                data = resp.json()
                media_id = data.get("media_id_string") or str(data.get("media_id"))
                return media_id
            else:
                logger.error(f"Twitter 图片上传失败 ({resp.status_code}): {resp.text}")
                return None
        except Exception as e:
            logger.error(f"Twitter 图片上传异常: {e}")
            return None

    @classmethod
    def post_tweet(
        cls, 
        text: str, 
        image_path: Optional[str] = None, 
        image_base64: Optional[str] = None,
        auth_override: Optional[OAuth1] = None
    ) -> Dict[str, Any]:
        """即时发布推文到 Twitter/X"""
        auth = auth_override or cls.get_auth()
        if not auth:
            return {
                "success": False, 
                "error": "未配置 Twitter API 授权信息，请先在【推特运营】设置中绑定 API Key 与 Access Token！"
            }

        if not text or not text.strip():
            return {"success": False, "error": "推文内容不能为空！"}

        # 确保推文文本彻底清理所有 HTML 标签并转换特殊实体（推特 v2 原生仅支持纯文本）
        clean_text = re.sub(r"<[^>]+>", "", text).strip()
        clean_text = clean_text.replace("&amp;", "&").replace("&quot;", '"').replace("&#39;", "'").replace("&lt;", "<").replace("&gt;", ">")

        media_id = None
        img_bytes = cls._extract_media_bytes(image_path=image_path, image_base64=image_base64)
        if img_bytes:
            media_id = cls.upload_media(auth, img_bytes)
            if not media_id:
                logger.warning("推特配图上传失败，将尝试纯文本发布")

        payload: Dict[str, Any] = {"text": clean_text}
        if media_id:
            payload["media"] = {"media_ids": [media_id]}

        try:
            resp = requests.post(
                TWITTER_V2_TWEET_URL,
                auth=auth,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=15
            )

            if resp.status_code in [200, 201]:
                res_data = resp.json().get("data", {})
                tweet_id = res_data.get("id")
                
                cfg = load_config()
                username = cfg.get("twitter", {}).get("account_info", {}).get("username", "i")
                tweet_url = f"https://x.com/{username}/status/{tweet_id}"

                return {
                    "success": True,
                    "tweet_id": tweet_id,
                    "text": res_data.get("text"),
                    "url": tweet_url
                }

            error_data = {}
            try:
                error_data = resp.json()
            except Exception:
                pass
            
            err_msg = error_data.get("detail") or error_data.get("title") or resp.text
            if "duplicate" in err_msg.lower():
                err_msg = "推特检测到重复内容 (Duplicate content)，请微调推文文字后再发布。"
            elif resp.status_code == 402 or "credits depleted" in err_msg.lower():
                err_msg = "推特账户余额不足 (402 credits depleted): 您在 X Developer Console 中的项目为 Pay Per Use (按量计费) 模式，请在 developer.x.com 左侧导航栏点击【Billing】->【Credits】充值少量额度。"
            elif resp.status_code == 403:
                err_msg = "发布权限受限 (403): 请检查 App 权限是否具有 'Write' 写入权限，或是否已超过推特每日发推频次上限。"

            return {
                "success": False,
                "error": f"发推失败 ({resp.status_code}): {err_msg}"
            }

        except Exception as e:
            logger.error(f"发推请求异常: {e}")
            return {"success": False, "error": f"发推网络异常: {str(e)}"}

    # ================= 自动发文排期 (Scheduled Pipeline) =================

    @classmethod
    def get_default_daily_schedules(cls) -> List[Dict[str, Any]]:
        """获取官方推荐的每日 3 次推特自动化发文排期 (10:00 白皮书卖点 / 14:30 区块链要闻 / 21:00 跨资产实时数据与量化观点)"""
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        return [
            {
                "id": "tw_daily_brand",
                "title": "🏛️ SparkOne 官方项目核心卖点 (白皮书/PPT深度)",
                "post_type": "sparkone_brand",
                "text": "🏛️ SPARK ONE: Institutional Pedigree Meets Web3\n\nBacked by SPARK UNION CAPITAL INC., SPARK ONE is bridging Wall Street hedge fund rigor with decentralized finance:\n\n• Multi-Tiered Asset Management: Institutional risk controls engineered from day one\n• Cross-Asset Coverage: Physical Gold (RWA), Sovereign Equities & Digital Assets\n• Regulatory Governance: Bank-grade custody with segregated cold-vault architecture\n\nDemolishing financial silos to democratize institutional alpha 🌐\n\n👉 Explore: https://sparkunioncapital.com/\n#SparkOne #AssetManagement #RWA #Web3 #FinTech",
                "image_filename": None,
                "image_base64": None,
                "scheduled_date": today_str,
                "scheduled_time": "10:00",
                "repeat": "daily",
                "enabled": True,
                "status": "pending",
                "last_executed": None,
                "tweet_id": None,
                "tweet_url": None,
                "error_msg": None,
                "created_at": now.strftime("%Y-%m-%d %H:%M:%S")
            },
            {
                "id": "tw_daily_crypto_news",
                "title": "⚡ 全球区块链重大新闻速递 (实时抓取+SPARK简析)",
                "post_type": "crypto_news",
                "text": "⚡ CRYPTO & BLOCKCHAIN HEADLINE BREAKING\n\nReal-time global crypto and institutional adoption news with SPARK AI quantitative perspective.\n\nStay ahead of macro market flows with SPARK ONE 🌐\n\n👉 Platform: https://sparkunioncapital.com/\n#CryptoNews #Bitcoin #Blockchain #Web3 #Macro #SparkOne",
                "image_filename": None,
                "image_base64": None,
                "scheduled_date": today_str,
                "scheduled_time": "14:30",
                "repeat": "daily",
                "enabled": True,
                "status": "pending",
                "last_executed": None,
                "tweet_id": None,
                "tweet_url": None,
                "error_msg": None,
                "created_at": now.strftime("%Y-%m-%d %H:%M:%S")
            },
            {
                "id": "tw_daily_market_alpha",
                "title": "📊 跨资产实时数据 (美股/代币/现货黄金) + SPARK量化投研观点",
                "post_type": "market_alpha",
                "text": "📊 SPARK ONE • GLOBAL ASSET RADAR & REAL-TIME DATA\n\n• Gold (RWA): Live bullion quote\n• Bitcoin / Ethereum: Real-time crypto quotes\n• NVIDIA / Apple: Wall Street equity beta\n\nSPARK AI Quant Outlook & Macro Alpha.\n\n👉 Platform: https://sparkunioncapital.com/\n#StockMarket #Crypto #Gold #QuantTrading #Alpha #SparkOne",
                "image_filename": None,
                "image_base64": None,
                "scheduled_date": today_str,
                "scheduled_time": "21:00",
                "repeat": "daily",
                "enabled": True,
                "status": "pending",
                "last_executed": None,
                "tweet_id": None,
                "tweet_url": None,
                "error_msg": None,
                "created_at": now.strftime("%Y-%m-%d %H:%M:%S")
            }
        ]

    @classmethod
    def reset_daily_3_schedules(cls) -> List[Dict[str, Any]]:
        """一键初始化/重置为每日 3 次全自动发文任务流水线"""
        defaults = cls.get_default_daily_schedules()
        cls.save_schedules(defaults)
        logger.info("✅ 已成功重置推特发文排期为官方每日 3 次全自动运营流水线")
        return defaults

    @classmethod
    def load_schedules(cls) -> List[Dict[str, Any]]:
        """读取所有已制定的自动发文排期任务"""
        path = cls._get_schedules_path()
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    schedules = json.load(f)
                    if isinstance(schedules, list) and len(schedules) > 0:
                        return schedules
            except Exception as e:
                logger.error(f"读取推特排期失败: {e}")

        # 如果没有排期，默认初始化官方每日 3 次全自动任务
        return cls.reset_daily_3_schedules()

    @classmethod
    def save_schedules(cls, schedules: List[Dict[str, Any]]) -> bool:
        """保存推特排期列表"""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(SCHEDULES_FILE, "w", encoding="utf-8") as f:
                json.dump(schedules, f, ensure_ascii=False, indent=2)
            return True
        except (OSError, PermissionError):
            try:
                with open(TMP_SCHEDULES_FILE, "w", encoding="utf-8") as f:
                    json.dump(schedules, f, ensure_ascii=False, indent=2)
                return True
            except Exception as e:
                logger.error(f"保存推特排期到 /tmp 失败: {e}")
                return False

    @classmethod
    def add_schedule(cls, item: Dict[str, Any]) -> Dict[str, Any]:
        """新增一条推特定时排期"""
        schedules = cls.load_schedules()
        now = datetime.now()
        new_item = {
            "id": f"tw_{int(now.timestamp())}_{len(schedules)+1}",
            "title": item.get("title") or "未命名推特排期",
            "post_type": item.get("post_type"), # "sparkone_brand" | "crypto_news" | "market_alpha" | None
            "text": item.get("text", "").strip(),
            "image_filename": item.get("image_filename"),
            "image_base64": item.get("image_base64"),
            "scheduled_date": item.get("scheduled_date") or now.strftime("%Y-%m-%d"),
            "scheduled_time": item.get("scheduled_time") or "10:00",
            "repeat": item.get("repeat") or "none", # "none" | "daily" | "weekly"
            "enabled": item.get("enabled", True),
            "status": "pending",
            "last_executed": None,
            "tweet_id": None,
            "tweet_url": None,
            "error_msg": None,
            "created_at": now.strftime("%Y-%m-%d %H:%M:%S")
        }
        schedules.insert(0, new_item)
        cls.save_schedules(schedules)
        return new_item

    @classmethod
    def update_schedule(cls, schedule_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """修改推特排期"""
        schedules = cls.load_schedules()
        for idx, item in enumerate(schedules):
            if item.get("id") == schedule_id:
                for k, v in updates.items():
                    if k != "id":
                        item[k] = v
                schedules[idx] = item
                cls.save_schedules(schedules)
                return item
        return None

    @classmethod
    def delete_schedule(cls, schedule_id: str) -> bool:
        """删除一条推特排期"""
        schedules = cls.load_schedules()
        filtered = [s for s in schedules if s.get("id") != schedule_id]
        if len(filtered) != len(schedules):
            cls.save_schedules(filtered)
            return True
        return False

    @classmethod
    def trigger_schedule_now(cls, schedule_id: str) -> Dict[str, Any]:
        """手动立即执行某一条推特排期"""
        schedules = cls.load_schedules()
        target = next((s for s in schedules if s.get("id") == schedule_id), None)
        if not target:
            return {"success": False, "error": "未找到指定的推特排期任务"}

        content_to_post = target.get("text", "")
        post_type = target.get("post_type")
        # 若设置了动态生成类型，即时生成最新鲜的内容（最新白皮书章节、最新突发新闻、最新实时行情）
        if post_type in ["sparkone_brand", "crypto_news", "market_alpha"]:
            try:
                gen = TwitterContentGenerator.generate_post(post_type)
                content_to_post = gen.get("text", content_to_post)
                target["text"] = content_to_post
            except Exception as e:
                logger.warning(f"动态生成最新推特内容失败，将使用预设文案: {e}")

        res = cls.post_tweet(
            text=content_to_post,
            image_path=target.get("image_filename"),
            image_base64=target.get("image_base64")
        )

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        target["last_executed"] = now_str
        if res.get("success"):
            target["status"] = "success"
            target["tweet_id"] = res.get("tweet_id")
            target["tweet_url"] = res.get("url")
            target["error_msg"] = None
        else:
            target["status"] = "failed"
            target["error_msg"] = res.get("error")

        cls.save_schedules(schedules)
        return res

    @classmethod
    def check_and_execute_due_tweets(cls) -> List[Dict[str, Any]]:
        """由调度器心跳每分钟轮询，扫描是否有已到期的推特排期并自动发布"""
        cfg = load_config()
        if not cfg.get("twitter", {}).get("enabled"):
            return []

        schedules = cls.load_schedules()
        now = datetime.now()
        executed_list = []
        changed = False

        for item in schedules:
            if not item.get("enabled"):
                continue

            # 仅处理待发送或周期循环的任务
            if item.get("status") not in ["pending", "failed"]:
                continue

            scheduled_date = item.get("scheduled_date")
            scheduled_time = item.get("scheduled_time")
            if not scheduled_date or not scheduled_time:
                continue

            try:
                due_dt = datetime.strptime(f"{scheduled_date} {scheduled_time}", "%Y-%m-%d %H:%M")
            except Exception:
                continue

            if now >= due_dt:
                logger.info(f"⏰ 触发推特到期自动发布任务: {item.get('title')} (ID: {item.get('id')})")
                item["status"] = "sending"

                content_to_post = item.get("text", "")
                post_type = item.get("post_type")
                # 动态生成：在到期执行瞬间实时抓取最新突发新闻或最新股票/代币/黄金行情
                if post_type in ["sparkone_brand", "crypto_news", "market_alpha"]:
                    try:
                        gen = TwitterContentGenerator.generate_post(post_type)
                        content_to_post = gen.get("text", content_to_post)
                        item["text"] = content_to_post
                    except Exception as e:
                        logger.warning(f"到期自动生成最新推特内容失败，将使用预设文案: {e}")

                res = cls.post_tweet(
                    text=content_to_post,
                    image_path=item.get("image_filename"),
                    image_base64=item.get("image_base64")
                )

                now_str = now.strftime("%Y-%m-%d %H:%M:%S")
                item["last_executed"] = now_str
                changed = True

                if res.get("success"):
                    item["tweet_id"] = res.get("tweet_id")
                    item["tweet_url"] = res.get("url")
                    item["error_msg"] = None

                    # 处理循环机制
                    repeat_type = item.get("repeat", "none")
                    if repeat_type == "daily":
                        # 推进到下一天
                        next_day = now + timedelta(days=1)
                        item["scheduled_date"] = next_day.strftime("%Y-%m-%d")
                        item["status"] = "pending"
                        logger.info(f"🔄 推特任务 【{item.get('title')}】 设为每日循环，下一次发送时间: {item['scheduled_date']} {item['scheduled_time']}")
                    elif repeat_type == "weekly":
                        next_week = now + timedelta(days=7)
                        item["scheduled_date"] = next_week.strftime("%Y-%m-%d")
                        item["status"] = "pending"
                        logger.info(f"🔄 推特任务 【{item.get('title')}】 设为每周循环，下一次发送时间: {item['scheduled_date']} {item['scheduled_time']}")
                    else:
                        item["status"] = "success"

                    executed_list.append({"id": item["id"], "success": True, "url": res.get("url")})
                else:
                    item["status"] = "failed"
                    item["error_msg"] = res.get("error")
                    executed_list.append({"id": item["id"], "success": False, "error": res.get("error")})

        if changed:
            cls.save_schedules(schedules)

        return executed_list

    @classmethod
    def get_templates(cls) -> List[Dict[str, Any]]:
        """获取推特精选高转化文案模版"""
        return DEFAULT_TWEET_TEMPLATES
