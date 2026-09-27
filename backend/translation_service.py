import httpx
import asyncio
from typing import Dict, Any, List, Optional
import json
import logging
import urllib.parse

logger = logging.getLogger(__name__)

class TranslationService:

    @classmethod
    async def translate_text(
        cls,
        text: str,
        target_lang: str,
        target_lang_name: str,
        engine: str = "built-in",
        api_key: str = "",
        model: str = "gemini-1.5-flash"
    ) -> str:
        """根据配置调用指定翻译引擎进行翻译"""
        if not text.strip():
            return ""

        engine = (engine or "built-in").lower()

        try:
            if engine == "gemini" and api_key:
                return await cls._translate_gemini(text, target_lang, target_lang_name, api_key, model)
            elif engine == "openai" and api_key:
                return await cls._translate_openai(text, target_lang, target_lang_name, api_key, model)
            elif engine == "deepl" and api_key:
                return await cls._translate_deepl(text, target_lang, api_key)
            else:
                # 备用或内置免费翻译
                return await cls._translate_builtin(text, target_lang)
        except Exception as e:
            logger.warning(f"翻译到 {target_lang} 遇到错误 ({engine}): {e}，尝试备用引擎...")
            try:
                return await cls._translate_builtin(text, target_lang)
            except Exception as e2:
                logger.error(f"备用翻译亦失败: {e2}")
                return f"[翻译错误: {e2}] {text}"

    @classmethod
    async def _translate_builtin(cls, text: str, target_lang: str) -> str:
        """免 API Key 的内置翻译接口 (Google Translate public endpoint)"""
        # 特殊语言代码映射
        lang_map = {
            "zh": "zh-CN",
            "ms": "ms",
            "id": "id",
            "vi": "vi",
            "th": "th",
            "ja": "ja",
            "ko": "ko",
            "ar": "ar",
            "pt": "pt",
            "es": "es",
            "en": "en"
        }
        tl = lang_map.get(target_lang, target_lang)
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "auto",
            "tl": tl,
            "dt": "t",
            "q": text
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            data = resp.json()
            # data 格式通常为 [[["翻译后的文本", "原文", ...]]]
            if data and isinstance(data, list) and data[0]:
                translated_chunks = [part[0] for part in data[0] if part and part[0]]
                return "".join(translated_chunks)
            return text

    @classmethod
    async def _translate_gemini(
        cls,
        text: str,
        target_lang: str,
        target_lang_name: str,
        api_key: str,
        model: str = "gemini-1.5-flash"
    ) -> str:
        """使用 Google Gemini 大模型进行地道翻译"""
        model_name = model or "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        prompt = (
            f"You are a professional multilingual translator for a global community (crypto, tech, markets, lifestyle).\n"
            f"Translate the following text into {target_lang_name} (Language code: {target_lang}).\n"
            f"Rules:\n"
            f"- Output ONLY the final translated text.\n"
            f"- Do NOT add explanations, intro words, or quotes.\n"
            f"- Preserve emojis, markdown formatting, bullet points, and links exactly.\n"
            f"- Keep tone engaging, authentic, and natural.\n\n"
            f"Content to translate:\n{text}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3}
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, json=payload)
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
            err = data.get("error", {}).get("message", "Gemini 翻译失败")
            raise RuntimeError(err)

    @classmethod
    async def _translate_openai(
        cls,
        text: str,
        target_lang: str,
        target_lang_name: str,
        api_key: str,
        model: str = "gpt-4o-mini"
    ) -> str:
        """使用 OpenAI 大模型进行翻译"""
        url = "https://api.openai.com/v1/chat/completions"
        model_name = model or "gpt-4o-mini"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        messages = [
            {
                "role": "system",
                "content": f"You are a professional translator. Translate all input text into {target_lang_name} ({target_lang}). Output ONLY translated text without quotes or explanations. Keep emojis and formatting intact."
            },
            {"role": "user", "content": text}
        ]
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.3
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            data = resp.json()
            if "choices" in data and data["choices"]:
                return data["choices"][0]["message"]["content"].strip()
            err = data.get("error", {}).get("message", "OpenAI 翻译失败")
            raise RuntimeError(err)

    @classmethod
    async def _translate_deepl(cls, text: str, target_lang: str, api_key: str) -> str:
        """使用 DeepL API 翻译"""
        endpoint = "https://api.deepl.com/v2/translate" if not api_key.endswith(":fx") else "https://api-free.deepl.com/v2/translate"
        headers = {"Authorization": f"DeepL-Auth-Key {api_key}"}
        # DeepL 目标语言规范化
        deepl_map = {
            "en": "EN-US",
            "pt": "PT-PT",
            "zh": "ZH",
            "es": "ES",
            "ja": "JA",
            "ko": "KO",
            "id": "ID"
        }
        target = deepl_map.get(target_lang, target_lang.upper())
        data = {
            "text": [text],
            "target_lang": target
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(endpoint, headers=headers, data=data)
            res_json = resp.json()
            translations = res_json.get("translations", [])
            if translations:
                return translations[0].get("text", "")
            raise RuntimeError(res_json.get("message", "DeepL 翻译失败"))

    @classmethod
    async def translate_batch(
        cls,
        text: str,
        topics: List[Dict[str, Any]],
        engine: str = "built-in",
        api_key: str = "",
        model: str = "gemini-1.5-flash"
    ) -> List[Dict[str, Any]]:
        """并发将一条文本翻译成所有启用的目标语言"""
        results = []

        async def _translate_single(topic: Dict[str, Any]):
            lang_code = topic.get("target_lang", "en")
            lang_name = topic.get("target_lang_name", "English")
            # 如果原文语言与目标语言相同，比如如果原输入是中文，且目标是中文
            translated = await cls.translate_text(
                text=text,
                target_lang=lang_code,
                target_lang_name=lang_name,
                engine=engine,
                api_key=api_key,
                model=model
            )
            return {
                "topic_id": topic["id"],
                "topic_name": topic["name"],
                "target_lang": lang_code,
                "target_lang_name": lang_name,
                "thread_id": topic.get("thread_id"),
                "translated_text": translated,
                "status": "ready"
            }

        # 仅针对启用的语言类话题做翻译
        target_topics = [t for t in topics if t.get("enabled", True) and t.get("category") == "language"]
        tasks = [_translate_single(t) for t in target_topics]
        results = await asyncio.gather(*tasks)
        return list(results)
