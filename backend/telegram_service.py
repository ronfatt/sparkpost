import httpx
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class TelegramService:
    BASE_URL = "https://api.telegram.org/bot{token}"

    @classmethod
    async def verify_bot(cls, token: str) -> Dict[str, Any]:
        """验证 Bot Token 是否有效"""
        url = f"{cls.BASE_URL.format(token=token)}/getMe"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(url)
                data = resp.json()
                if data.get("ok"):
                    return {"success": True, "bot": data["result"]}
                return {"success": False, "error": data.get("description", "Unknown error")}
            except Exception as e:
                return {"success": False, "error": str(e)}

    @classmethod
    async def send_message(
        cls,
        token: str,
        chat_id: str,
        text: str,
        thread_id: Optional[int] = None,
        parse_mode: str = "HTML",
        retry_count: int = 3
    ) -> Dict[str, Any]:
        """向指定群组的指定话题 (Topic) 发送消息，内置 429 限流自愈与重试"""
        url = f"{cls.BASE_URL.format(token=token)}/sendMessage"
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": False
        }
        if thread_id is not None and int(thread_id) > 0:
            payload["message_thread_id"] = int(thread_id)

        async with httpx.AsyncClient(timeout=15.0) as client:
            for attempt in range(retry_count):
                try:
                    resp = await client.post(url, json=payload)
                    data = resp.json()
                    
                    if data.get("ok"):
                        return {"success": True, "message_id": data["result"]["message_id"]}
                    
                    # 遇到 429 限流，提取 retry_after 并等待
                    if resp.status_code == 429 or "too many requests" in data.get("description", "").lower():
                        retry_after = data.get("parameters", {}).get("retry_after", 2)
                        logger.warning(f"触发 Telegram 限流，等待 {retry_after} 秒后重试...")
                        import asyncio
                        await asyncio.sleep(retry_after + 0.5)
                        continue

                    # 如果是 parse_mode 报错，降级为纯文本重试
                    if "can't parse entities" in data.get("description", "").lower():
                        payload.pop("parse_mode", None)
                        retry_resp = await client.post(url, json=payload)
                        retry_data = retry_resp.json()
                        if retry_data.get("ok"):
                            return {"success": True, "message_id": retry_data["result"]["message_id"]}
                    
                    return {"success": False, "error": data.get("description", "Unknown error")}
                except Exception as e:
                    if attempt == retry_count - 1:
                        return {"success": False, "error": str(e)}
                    import asyncio
                    await asyncio.sleep(1.0)
            return {"success": False, "error": "Exceeded retry limit"}

    @classmethod
    async def send_photo(
        cls,
        token: str,
        chat_id: str,
        photo_bytes: bytes,
        filename: str,
        caption: Optional[str] = None,
        thread_id: Optional[int] = None,
        parse_mode: str = "HTML"
    ) -> Dict[str, Any]:
        """向指定话题发送带图片的广播"""
        url = f"{cls.BASE_URL.format(token=token)}/sendPhoto"
        data: Dict[str, Any] = {
            "chat_id": chat_id,
            "parse_mode": parse_mode
        }
        if caption:
            data["caption"] = caption
        if thread_id is not None and int(thread_id) > 0:
            data["message_thread_id"] = str(thread_id)

        files = {"photo": (filename, photo_bytes, "image/jpeg")}

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(url, data=data, files=files)
                res_json = resp.json()
                if res_json.get("ok"):
                    return {"success": True, "message_id": res_json["result"]["message_id"]}
                return {"success": False, "error": res_json.get("description", "Unknown error")}
            except Exception as e:
                return {"success": False, "error": str(e)}

    @classmethod
    async def detect_topics_from_updates(cls, token: str) -> Dict[str, Any]:
        """
        通过 getUpdates 自动侦测群里的消息和话题 (Topics)
        用户在各个 Topic 话题下发一条消息（例如打字 'test'），点击此按钮即可自动识别其 thread_id！
        """
        url = f"{cls.BASE_URL.format(token=token)}/getUpdates?limit=50"
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(url)
                data = resp.json()
                if not data.get("ok"):
                    return {"success": False, "error": data.get("description", "获取更新失败")}
                
                updates = data.get("result", [])
                detected_chats = {}
                detected_topics = {}

                for u in updates:
                    msg = u.get("message") or u.get("channel_post") or u.get("edited_message")
                    if not msg:
                        continue
                    chat = msg.get("chat", {})
                    chat_id = chat.get("id")
                    chat_title = chat.get("title", "未命名群组")
                    if chat_id:
                        detected_chats[str(chat_id)] = chat_title

                    # 检查是否有 topic / thread
                    thread_id = msg.get("message_thread_id")
                    # 论坛话题创建事件
                    topic_created = msg.get("forum_topic_created")
                    topic_title = None
                    if topic_created:
                        topic_title = topic_created.get("name")
                    
                    if thread_id:
                        sender_text = msg.get("text") or msg.get("caption") or "[附件/事件]"
                        detected_topics[str(thread_id)] = {
                            "thread_id": thread_id,
                            "chat_id": chat_id,
                            "chat_title": chat_title,
                            "topic_name": topic_title or f"话题 #{thread_id}",
                            "last_message": sender_text[:30]
                        }

                return {
                    "success": True,
                    "detected_chats": [{"id": cid, "title": title} for cid, title in detected_chats.items()],
                    "detected_topics": list(detected_topics.values())
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
