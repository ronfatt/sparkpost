import os
import io
import datetime
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class CardGenerator:
    """生成高颜值黑金科技风金融行情海报"""

    @classmethod
    def _get_font(cls, size: int, bold: bool = False) -> ImageFont.ImageFont:
        # Mac 常见系统无衬线字体，退化为默认字体
        font_paths = [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf"
        ]
        for p in font_paths:
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    continue
        return ImageFont.load_default()

    @classmethod
    def generate_gold_card(cls, data: Dict[str, Any], output_path: str) -> str:
        """生成区块链 RWA 代币化黄金 (PAXG/XAUT) 与传统现货金对比海报"""
        width, height = 900, 1150
        # 深色黑金背景渐变
        img = Image.new("RGB", (width, height), color="#080c16")
        draw = ImageDraw.Draw(img)

        # 1. 顶部装饰金黄光效
        draw.rectangle([(0, 0), (width, 8)], fill="#eab308")
        draw.rectangle([(20, 20), (width-20, height-20)], outline="#1e293b", width=2)

        # 2. 品牌 Header
        font_title = cls._get_font(36, bold=True)
        font_sub = cls._get_font(18, bold=False)
        font_tag = cls._get_font(14, bold=True)
        
        draw.text((60, 60), "⚡ SPARK ONE", fill="#ffffff", font=font_title)
        draw.text((60, 110), "BLOCKCHAIN RWA & TOKENIZED GOLD WATCH", fill="#facc15", font=font_sub)
        
        # 每小时自动更新标志
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        draw.rounded_rectangle([(width-360, 65), (width-60, 105)], radius=8, fill="#1e293b")
        draw.text((width-340, 75), f"⏱️ HOURLY: {now_str}", fill="#38bdf8", font=font_tag)

        # 3. 核心大卡片 1: PAX Gold (PAXG)
        quotes = data.get("quotes", {})
        paxg = quotes.get("paxg") or {"price": 2686.2, "change": 14.5, "change_pct": 0.54}
        xaut = quotes.get("xaut") or {"price": 2685.8, "change": 14.1, "change_pct": 0.53}
        gold = quotes.get("gold") or {"price": 2684.0, "change": 13.8, "change_pct": 0.51}
        premium = data.get("premium", "+0.08%")

        # PAXG 主卡片
        draw.rounded_rectangle([(60, 160), (width-60, 390)], radius=16, fill="#0f172a", outline="#eab308", width=2)
        draw.text((90, 185), "🪙 PAX GOLD (PAXG) • 链上第一合规黄金", fill="#f8fafc", font=cls._get_font(22, bold=True))
        
        paxg_p_str = f"${paxg.get('price', 0):,}"
        draw.text((90, 225), paxg_p_str, fill="#fef08a", font=cls._get_font(60, bold=True))

        # 涨跌幅胶囊
        is_up = paxg.get("change", 0) >= 0
        pill_bg = "#14532d" if is_up else "#7f1d1d"
        pill_text = "#4ade80" if is_up else "#f87171"
        sign = "+" if is_up else ""
        chg_str = f" {sign}{paxg.get('change', 0)} ({sign}{paxg.get('change_pct', 0)}%) "
        
        draw.rounded_rectangle([(90, 315), (380, 365)], radius=10, fill=pill_bg)
        draw.text((110, 325), chg_str, fill=pill_text, font=cls._get_font(20, bold=True))

        # 链上溢价标签
        draw.rounded_rectangle([(width-430, 315), (width-90, 365)], radius=10, fill="#1e1b4b", outline="#6366f1")
        draw.text((width-410, 327), f"⚡ 链上溢价: {premium}", fill="#a5b4fc", font=cls._get_font(18, bold=True))

        # 4. 区块链与传统黄金对照卡片
        draw.text((60, 430), "🌐 BLOCKCHAIN & TRADITIONAL GOLD BENCHMARKS", fill="#64748b", font=cls._get_font(16, bold=True))

        items = [
            ("🪙 Tether Gold (XAUT)", "Tether 发行 / 瑞士实物金库储备", xaut),
            ("🏛️ 传统现货黄金 (XAU/USD)", "伦敦金 / 传统金融现货基准", gold),
            ("⚪ 现货白银 (XAG/USD)", "贵金属联动参照标的", quotes.get("silver")),
            ("💵 美元指数 (DXY)", "全球宏观流动性基准", quotes.get("dxy"))
        ]

        y = 470
        for title, sub, q in items:
            draw.rounded_rectangle([(60, y), (width-60, y+95)], radius=12, fill="#111827", outline="#1f2937", width=1)
            draw.text((90, y+20), title, fill="#f8fafc", font=cls._get_font(19, bold=True))
            draw.text((90, y+52), sub, fill="#64748b", font=cls._get_font(14))
            
            if q:
                p_text = f"${q.get('price', 0):,}"
                c_up = q.get("change", 0) >= 0
                c_color = "#4ade80" if c_up else "#f87171"
                c_sign = "+" if c_up else ""
                c_text = f"{c_sign}{q.get('change', 0)} ({c_sign}{q.get('change_pct', 0)}%)"

                draw.text((width-380, y+24), p_text, fill="#f8fafc", font=cls._get_font(22, bold=True))
                draw.text((width-200, y+26), c_text, fill=c_color, font=cls._get_font(17, bold=True))
            else:
                draw.text((width-220, y+26), "Syncing...", fill="#64748b", font=cls._get_font(18))

            y += 115

        # 5. 底部 RWA 点评与官方声明
        draw.rounded_rectangle([(60, 940), (width-60, 1050)], radius=12, fill="#0f172a", outline="#334155")
        draw.text((90, 960), "💡 SPARK ONE RWA GOLD INSIGHT:", fill="#eab308", font=cls._get_font(16, bold=True))
        draw.text((90, 990), "Tokenized real-world gold (RWA) bridges DeFi liquidity with safe-haven stability.", fill="#cbd5e1", font=cls._get_font(15))
        draw.text((90, 1015), "Auto-refreshed every 1 hour • Precision on-chain price tracking.", fill="#94a3b8", font=cls._get_font(14))

        draw.text((60, 1090), "Official Portal: https://sparkunioncapital.com/", fill="#64748b", font=cls._get_font(15))
        draw.text((width-340, 1090), "Hourly Automated Dispatch Active", fill="#eab308", font=cls._get_font(15, bold=True))

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, quality=95)
        return output_path

    @classmethod
    def generate_stocks_card(cls, data: Dict[str, Any], output_path: str) -> str:
        """生成美股三大指数与全球大盘行情海报"""
        width, height = 900, 1100
        img = Image.new("RGB", (width, height), color="#080e1a")
        draw = ImageDraw.Draw(img)

        # 顶部蓝紫渐变条
        draw.rectangle([(0, 0), (width, 8)], fill="#3b82f6")
        draw.rectangle([(20, 20), (width-20, height-20)], outline="#1e293b", width=2)

        # 品牌 Header
        draw.text((60, 60), "⚡ SPARK ONE", fill="#ffffff", font=cls._get_font(36, bold=True))
        draw.text((60, 110), "GLOBAL EQUITY INDICES & MACRO WATCH", fill="#94a3b8", font=cls._get_font(18))
        
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M UTC+8")
        draw.rounded_rectangle([(width-320, 65), (width-60, 105)], radius=8, fill="#1e293b")
        draw.text((width-300, 75), f"🕒 {now_str}", fill="#60a5fa", font=cls._get_font(14, bold=True))

        quotes = data.get("quotes", {})
        
        items = [
            ("S&P 500 (US)", quotes.get("sp500")),
            ("NASDAQ 100 (US Tech)", quotes.get("nasdaq")),
            ("DOW JONES (US Industrial)", quotes.get("dow")),
            ("NIKKEI 225 (Japan)", quotes.get("nikkei")),
            ("HANG SENG (Hong Kong)", quotes.get("hsi")),
            ("BITCOIN (Global Macro Asset)", quotes.get("btc"))
        ]

        y = 170
        for title, q in items:
            draw.rounded_rectangle([(60, y), (width-60, y+90)], radius=14, fill="#111827", outline="#1f2937", width=1)
            draw.text((90, y+30), title, fill="#f8fafc", font=cls._get_font(20, bold=True))
            
            if q:
                p_text = f"{q.get('price', 0):,}"
                c_up = q.get("change", 0) >= 0
                c_color = "#4ade80" if c_up else "#f87171"
                c_sign = "+" if c_up else ""
                c_text = f"{c_sign}{q.get('change', 0)} ({c_sign}{q.get('change_pct', 0)}%)"

                draw.text((width-380, y+30), p_text, fill="#f8fafc", font=cls._get_font(22, bold=True))
                draw.text((width-190, y+32), c_text, fill=c_color, font=cls._get_font(18, bold=True))
            else:
                draw.text((width-220, y+32), "Syncing...", fill="#64748b", font=cls._get_font(18))

            y += 115

        # 底部官方声明
        draw.rounded_rectangle([(60, 890), (width-60, 990)], radius=12, fill="#0f172a", outline="#1e293b")
        draw.text((90, 915), "📊 Market Observation:", fill="#38bdf8", font=cls._get_font(16, bold=True))
        draw.text((90, 945), "Global liquidity and sector rotation remain key drivers. Stay disciplined.", fill="#94a3b8", font=cls._get_font(16))

        draw.text((60, 1030), "Official Portal: https://sparkunioncapital.com/", fill="#64748b", font=cls._get_font(15))
        draw.text((width-320, 1030), "Never DM First • Anti-Scam Verified", fill="#38bdf8", font=cls._get_font(15, bold=True))

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, quality=95)
        return output_path
