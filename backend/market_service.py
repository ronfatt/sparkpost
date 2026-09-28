import datetime
import random
from typing import Dict, Any, List, Optional
import logging
import asyncio

logger = logging.getLogger(__name__)

class MarketService:
    """
    全球跨资产行情与轮动分发服务 (Bloomberg x Quant Desk Style)
    为 Telegram 专属话题打造：
    - Thread #7: 贵金属与 RWA 黄金矩阵 (Gold + 轮动白银/铂金/钯金)
    - Thread #8: 全球大盘雷达 (三大指数 + 轮动 3~4 支核心股票 + 轮动 1~2 种大宗商品 + 轮动 1~2 种外汇)
    - Thread #5: 加密资产与 AI 宏观脉搏 (BTC/ETH + 轮动优质公链)
    """

    # 1. 贵金属轮动池
    PRECIOUS_METALS_ROTATION = [
        {"symbol": "SI=F", "id": "XAG", "name": "Spot Silver (XAG/USD)", "unit": "oz", "note": "High industrial beta & solar demand driver"},
        {"symbol": "PL=F", "id": "XPT", "name": "Spot Platinum (XPT/USD)", "unit": "oz", "note": "Catalytic converter & green hydrogen catalyst"},
        {"symbol": "PA=F", "id": "XPD", "name": "Spot Palladium (XPD/USD)", "unit": "oz", "note": "Automotive electronics & structural deficit watch"}
    ]

    # 2. 股票 23 支标的按 3 大赛道主题编组 (每次智能轮选一个主题，精选 3~4 支)
    STOCK_THEMES = [
        {
            "theme_id": "ai_semis",
            "theme_name": "⚡ AI & Semiconductor Titans",
            "stocks": [
                {"symbol": "NVDA", "name": "NVIDIA", "desc": "AI Datacenter GPU & Blackwell demand"},
                {"symbol": "TSM", "name": "TSMC ADR", "desc": "Leading-edge 3nm/2nm foundry capacity"},
                {"symbol": "ASML", "name": "ASML Holding", "desc": "EUV lithography orders & fab expansion"},
                {"symbol": "AVGO", "name": "Broadcom", "desc": "Custom AI ASIC & networking cluster"},
                {"symbol": "AMD", "name": "AMD", "desc": "Instinct MI300 series cloud enterprise adoption"},
                {"symbol": "QCOM", "name": "Qualcomm", "desc": "On-device GenAI & Snapdragon automotive"},
                {"symbol": "MRVL", "name": "Marvell Tech", "desc": "High-speed electro-optics interconnects"},
                {"symbol": "INTC", "name": "Intel", "desc": "IFS foundry buildout & x86 client recovery"},
                {"symbol": "MU", "name": "Micron Tech", "desc": "HBM3E high-bandwidth memory allocation"}
            ]
        },
        {
            "theme_id": "us_megacap",
            "theme_name": "🏛️ US Mega-Cap Tech Leaders",
            "stocks": [
                {"symbol": "AAPL", "name": "Apple", "desc": "Services ecosystem & Apple Intelligence suite"},
                {"symbol": "MSFT", "name": "Microsoft", "desc": "Azure Cloud AI & enterprise Copilot scaling"},
                {"symbol": "GOOGL", "name": "Alphabet (Google)", "desc": "Gemini models & Google Cloud run-rate"},
                {"symbol": "AMZN", "name": "Amazon", "desc": "AWS cloud capex surge & retail efficiency"},
                {"symbol": "META", "name": "Meta Platforms", "desc": "Open-source Llama & AI-driven ad monetization"},
                {"symbol": "TSLA", "name": "Tesla", "desc": "Autonomous FSD network & Megapack storage"}
            ]
        },
        {
            "theme_id": "asia_leaders",
            "theme_name": "🌏 Asia & Global Tech Giants",
            "stocks": [
                {"symbol": "0700.HK", "name": "Tencent (腾讯)", "desc": "Gaming monetization & WeChat cloud ecosystem"},
                {"symbol": "BABA", "name": "Alibaba (阿里巴巴)", "desc": "Cloud Intelligence group turnaround & AI models"},
                {"symbol": "1810.HK", "name": "Xiaomi (小米)", "desc": "EV scale ramp-up & global smartphone share"},
                {"symbol": "3690.HK", "name": "Meituan (美团)", "desc": "Core local commerce efficiency & international scale"},
                {"symbol": "2330.TW", "name": "TSMC (台积电)", "desc": "Advanced CoWoS packaging capacity expansion"},
                {"symbol": "005930.KS", "name": "Samsung Electronics", "desc": "Next-gen HBM3E memory qualification progress"},
                {"symbol": "SONY", "name": "Sony Group", "desc": "CIS sensor market leadership & PlayStation network"},
                {"symbol": "0981.HK", "name": "SMIC (中芯国际)", "desc": "Domestic semiconductor fabrication capacity"}
            ]
        }
    ]

    # 3. 大宗商品池：能源 (每次轮动 1 种)
    COMMODITIES_ENERGY = [
        {"symbol": "CL=F", "id": "WTI", "name": "WTI Crude Oil", "unit": "$/bbl", "note": "Global crude benchmark & inventory balance"},
        {"symbol": "BZ=F", "id": "Brent", "name": "Brent Crude Oil", "unit": "$/bbl", "note": "Seaborne crude price & OPEC+ supply quota"},
        {"symbol": "NG=F", "id": "NG", "name": "Natural Gas", "unit": "$/MMBtu", "note": "Weather outlook & power generation feed"}
    ]

    # 4. 大宗商品池：工业金属与农产品 (每次轮动 1 种)
    COMMODITIES_IND_AGRI = [
        {"symbol": "HG=F", "id": "HG", "name": "Copper (HG)", "unit": "$/lb", "note": "Doctor Copper: global manufacturing bellwether"},
        {"symbol": "ALI=F", "id": "AL", "name": "Aluminum (AL)", "unit": "$/t", "note": "Lightweight EV and industrial metallurgy demand"},
        {"symbol": "ZC=F", "id": "ZC", "name": "Corn (ZC)", "unit": "¢/bu", "note": "Feed grain supply & ethanol refining demand"},
        {"symbol": "ZW=F", "id": "ZW", "name": "Wheat (ZW)", "unit": "¢/bu", "note": "Global food security & weather export bottlenecks"},
        {"symbol": "ZS=F", "id": "ZS", "name": "Soybeans (ZS)", "unit": "¢/bu", "note": "Crush margin and South American export volume"},
        {"symbol": "CT=F", "id": "CT", "name": "Cotton (CT)", "unit": "¢/lb", "note": "Textile manufacturing index & harvest yield"},
        {"symbol": "SB=F", "id": "SB", "name": "Sugar #11 (SB)", "unit": "¢/lb", "note": "Cane harvest season and biofuel diversion"},
        {"symbol": "KC=F", "id": "KC", "name": "Coffee (KC)", "unit": "¢/lb", "note": "Rainfall cycles & Arabica export supply tightness"}
    ]

    # 5. 外汇交易对池 (每次轮动 2 种)
    FOREX_PAIRS = [
        {"symbol": "EURUSD=X", "name": "EUR/USD", "note": "ECB policy stance vs Fed rate trajectory"},
        {"symbol": "JPY=X", "name": "USD/JPY", "note": "BoJ yield curve control & carry unwind focus"},
        {"symbol": "GBPUSD=X", "name": "GBP/USD", "note": "Bank of England policy & UK economic resilience"},
        {"symbol": "CHF=X", "name": "USD/CHF", "note": "Safe-haven capital allocation channel"},
        {"symbol": "CAD=X", "name": "USD/CAD", "note": "Crude oil pricing correlation & Bank of Canada"},
        {"symbol": "AUDUSD=X", "name": "AUD/USD", "note": "Commodity trade proxy & China macro demand"},
        {"symbol": "NZDUSD=X", "name": "NZD/USD", "note": "RBNZ cash rate & dairy export flow"},
        {"symbol": "EURGBP=X", "name": "EUR/GBP", "note": "Cross-rate European economic differential"},
        {"symbol": "EURJPY=X", "name": "EUR/JPY", "note": "Cross-currency carry trade risk barometer"},
        {"symbol": "GBPJPY=X", "name": "GBP/JPY", "note": "High-beta global risk appetite cross"},
        {"symbol": "EURCHF=X", "name": "EUR/CHF", "note": "European defensive balance barometer"},
        {"symbol": "AUDJPY=X", "name": "AUD/JPY", "note": "Classic global risk-on / risk-off spread"},
        {"symbol": "CNH=X", "name": "USD/CNH", "note": "Offshore RMB liquidity & PBOC fixing trend"}
    ]

    # 6. 加密资产池 (BTC/ETH 锚点 + 轮动 2 种优质公链代币)
    CRYPTO_ASSETS = [
        {"symbol": "BTC-USD", "id": "BTC", "name": "Bitcoin (BTC)", "role": "Digital Gold & Macro Anchor"},
        {"symbol": "ETH-USD", "id": "ETH", "name": "Ethereum (ETH)", "role": "Smart Contract Settlement Layer"},
        {"symbol": "SOL-USD", "id": "SOL", "name": "Solana (SOL)", "role": "High-Throughput DeFi & Consumer Web3"},
        {"symbol": "BNB-USD", "id": "BNB", "name": "BNB Chain (BNB)", "role": "Exchange Ecosystem & On-chain Liquidity"},
        {"symbol": "XRP-USD", "id": "XRP", "name": "XRP", "role": "Cross-Border Liquidity & Remittance Rail"},
        {"symbol": "ADA-USD", "id": "ADA", "name": "Cardano (ADA)", "role": "Peer-Reviewed Proof-of-Stake Network"},
        {"symbol": "DOGE-USD", "id": "DOGE", "name": "Dogecoin (DOGE)", "role": "Retail Volume & Social Liquidity Index"},
        {"symbol": "TRX-USD", "id": "TRX", "name": "TRON (TRX)", "role": "Global Stablecoin Transfer Volume Leader"}
    ]

    @classmethod
    def _fetch_quote_sync(cls, symbol: str) -> Optional[Dict[str, Any]]:
        """使用 yfinance 同步拉取单个标的数据"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            fast = ticker.fast_info
            price = fast.last_price
            prev = fast.previous_close
            if price is None:
                return None
            
            change = price - prev if prev else 0.0
            change_pct = (change / prev * 100) if prev else 0.0
            high = fast.day_high or price
            low = fast.day_low or price

            return {
                "symbol": symbol,
                "price": round(price, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "day_high": round(high, 2),
                "day_low": round(low, 2),
                "currency": fast.currency or "USD"
            }
        except Exception as e:
            logger.warning(f"拉取 {symbol} 失败: {e}")
            return None

    @classmethod
    def _fetch_quotes_batch_sync(cls, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """批量极速拉取标的行情"""
        results = {}
        try:
            import yfinance as yf
            tickers = yf.Tickers(" ".join(symbols))
            for sym in symbols:
                try:
                    t = tickers.tickers.get(sym)
                    if t and t.fast_info.last_price:
                        fi = t.fast_info
                        p = fi.last_price
                        prev = fi.previous_close or p
                        chg = p - prev
                        chg_pct = (chg / prev * 100) if prev else 0.0
                        results[sym] = {
                            "symbol": sym,
                            "price": round(p, 2),
                            "change": round(chg, 2),
                            "change_pct": round(chg_pct, 2)
                        }
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"批量拉取行情异常: {e}")
        return results

    # ================= 业务方法 1: Thread #7 贵金属与 RWA 黄金矩阵 =================

    @classmethod
    async def get_gold_market_data(cls) -> Dict[str, Any]:
        """
        Thread #7 专属：贵金属与区块链 RWA 黄金矩阵
        - 固定锚点：PAX Gold (PAXG), Tether Gold (XAUT), 现货黄金 XAU/USD
        - 轮动抽取：随机挑选 1 种其他贵金属 (白银 XAG / 铂金 XPT / 钯金 XPD) 进行比价与联动
        """
        loop = asyncio.get_event_loop()

        # 随机抽取 1 个次要贵金属
        rotated_pm = random.choice(cls.PRECIOUS_METALS_ROTATION)

        symbols_to_fetch = [
            "PAXG-USD",  # Pax Gold
            "XAUT-USD",  # Tether Gold
            "GC=F",      # Spot Gold XAU/USD
            rotated_pm["symbol"],  # 轮选的贵金属
            "DX-Y.NYB"   # US Dollar Index
        ]

        quotes = await loop.run_in_executor(None, cls._fetch_quotes_batch_sync, symbols_to_fetch)
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        paxg_q = quotes.get("PAXG-USD")
        xaut_q = quotes.get("XAUT-USD")
        gold_q = quotes.get("GC=F")
        rot_q = quotes.get(rotated_pm["symbol"])
        dxy_q = quotes.get("DX-Y.NYB")

        def fmt_change(q):
            if not q:
                return "Data Syncing"
            icon = "🟢 +" if q["change"] >= 0 else "🔴 "
            return f"{icon}{q['change']} ({q['change_pct']}%)"

        def fmt_price(q, fallback):
            if q and q.get("price"):
                return f"${q['price']:,}"
            return fallback

        # 计算 RWA 黄金溢价率
        premium_str = "+0.00%"
        if paxg_q and gold_q and gold_q["price"] > 0:
            diff = paxg_q["price"] - gold_q["price"]
            diff_pct = (diff / gold_q["price"]) * 100
            p_sign = "+" if diff_pct >= 0 else ""
            premium_str = f"{p_sign}{round(diff_pct, 2)}%"

        # 计算金银比或金/贵金属比价
        ratio_line = ""
        if gold_q and rot_q and rot_q["price"] > 0:
            ratio = round(gold_q["price"] / rot_q["price"], 1)
            ratio_line = f"📊 <b>Gold/{rotated_pm['id']} Ratio:</b> <code>{ratio}x</code> <i>({rotated_pm['note']})</i>\n"

        text = (
            f"🥇 <b>SPARK ONE • Precious Metals & Tokenized RWA Watch</b>\n"
            f"🕒 <i>Hourly Market Update | Time: {now_str}</i>\n\n"
            f"<b>【TOKENIZED RWA GOLD (BLOCKCHAIN)】</b>\n"
            f"🪙 <b>PAX Gold (PAXG):</b> <b>{fmt_price(paxg_q, '$2,685.00')}</b> | {fmt_change(paxg_q)}\n"
            f"   ↳ <i>Paxos Issued • 100% Backed by London Good Delivery Physical Gold</i>\n"
            f"🪙 <b>Tether Gold (XAUT):</b> <b>{fmt_price(xaut_q, '$2,686.00')}</b> | {fmt_change(xaut_q)}\n"
            f"   ↳ <i>Tether Issued • Backed by Physical Swiss Vault Reserves</i>\n\n"
            f"<b>【SPOT BENCHMARK & SPREAD】</b>\n"
            f"🏛️ <b>Spot Gold (XAU/USD):</b> <b>{fmt_price(gold_q, '$2,684.00')}</b> | {fmt_change(gold_q)}\n"
            f"⚡ <b>On-Chain Gold Premium:</b> <code>{premium_str}</code>\n\n"
            f"<b>【ROTATED PRECIOUS METAL & MACRO】</b>\n"
            f"✨ <b>{rotated_pm['name']}:</b> <b>{fmt_price(rot_q, '-')}</b> | {fmt_change(rot_q)}\n"
            f"{ratio_line}"
            f"💵 <b>US Dollar Index (DXY):</b> <b>{dxy_q['price'] if dxy_q else '101.4'}</b> | {fmt_change(dxy_q)}\n\n"
            f"💡 <b>Institutional Intelligence:</b>\n"
            f"Tokenized gold liquidity pools remain highly liquid. Capital allocation reflects sustained institutional interest in on-chain real-world store of value.\n\n"
            f"#Gold #PreciousMetals #RWA #PAXG #XAUT #Commodities #SparkOne"
        )

        return {
            "title": f"Precious Metals & Tokenized Gold ({rotated_pm['id']} Featured)",
            "type": "gold",
            "quotes": quotes,
            "premium": premium_str,
            "rotated_asset": rotated_pm,
            "telegram_message": text,
            "generated_at": now_str
        }

    # ================= 业务方法 2: Thread #8 全球大盘雷达 (股票+大宗+外汇智能抽取) =================

    @classmethod
    async def get_global_stocks_data(cls) -> Dict[str, Any]:
        """
        Thread #8 专属：全球大盘雷达 (股票、大宗商品、外汇轮动抽取)
        - 核心指数：标普500 (S&P 500)、纳斯达克 (Nasdaq)、恒生 (Hang Seng)
        - 股票轮动：从 23 支股票中按赛道抽取 3~4 支 (AI芯片 / 美股巨头 / 亚太科技)
        - 大宗轮动：抽取 1 种能源 (WTI/Brent/NG) + 1 种工业金属或农产品 (铜/铝/粮食)
        - 外汇轮动：抽取 2 种主要交易对 (EUR/USD, USD/JPY, USD/CNH 等)
        """
        loop = asyncio.get_event_loop()

        # 1. 智能抽取股票主题与 3~4 支标的
        chosen_theme = random.choice(cls.STOCK_THEMES)
        stock_count = 4 if len(chosen_theme["stocks"]) >= 4 else len(chosen_theme["stocks"])
        picked_stocks = random.sample(chosen_theme["stocks"], stock_count)

        # 2. 智能抽取大宗商品
        picked_energy = random.choice(cls.COMMODITIES_ENERGY)
        picked_ind_agri = random.choice(cls.COMMODITIES_IND_AGRI)

        # 3. 智能抽取 2 组外汇交易对
        picked_forex = random.sample(cls.FOREX_PAIRS, 2)

        # 4. 汇总需要拉取行情的全部标的
        symbols_to_fetch = [
            "^GSPC",   # S&P 500
            "^IXIC",   # Nasdaq
            "^HSI",    # Hang Seng Index
            picked_energy["symbol"],
            picked_ind_agri["symbol"]
        ]
        for s in picked_stocks:
            symbols_to_fetch.append(s["symbol"])
        for f in picked_forex:
            symbols_to_fetch.append(f["symbol"])

        quotes = await loop.run_in_executor(None, cls._fetch_quotes_batch_sync, symbols_to_fetch)
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        def fmt_item(name, q, unit=""):
            if not q or not q.get("price"):
                return f"• {name}: Data Syncing..."
            icon = "🟢 +" if q["change"] >= 0 else "🔴 "
            u_str = f" {unit}" if unit else ""
            return f"• <b>{name}</b>: <b>{q['price']:,}{u_str}</b> ({icon}{q['change_pct']}%)"

        # 格式化指数板块
        indices_section = (
            f"<b>【MAJOR GLOBAL INDICES】</b>\n"
            f"{fmt_item('S&P 500 (US)', quotes.get('^GSPC'))}\n"
            f"{fmt_item('Nasdaq 100 (Tech)', quotes.get('^IXIC'))}\n"
            f"{fmt_item('Hang Seng Index (HK)', quotes.get('^HSI'))}\n"
        )

        # 格式化股票轮动板块
        stocks_lines = []
        for s in picked_stocks:
            q = quotes.get(s["symbol"])
            stocks_lines.append(f"{fmt_item(s['name'], q)}  <i>↳ {s['desc']}</i>")
        stocks_section = (
            f"<b>【FEATURED STOCKS • {chosen_theme['theme_name']}】</b>\n"
            + "\n".join(stocks_lines) + "\n"
        )

        # 格式化大宗商品轮动板块
        comms_section = (
            f"<b>【MACRO COMMODITIES FOCUS】</b>\n"
            f"{fmt_item(picked_energy['name'], quotes.get(picked_energy['symbol']), picked_energy['unit'])}  <i>↳ {picked_energy['note']}</i>\n"
            f"{fmt_item(picked_ind_agri['name'], quotes.get(picked_ind_agri['symbol']), picked_ind_agri['unit'])}  <i>↳ {picked_ind_agri['note']}</i>\n"
        )

        # 格式化外汇轮动板块
        fx_lines = []
        for f in picked_forex:
            q = quotes.get(f["symbol"])
            fx_lines.append(f"{fmt_item(f['name'], q)}  <i>↳ {f['note']}</i>")
        forex_section = (
            f"<b>【FOREIGN EXCHANGE (FX) PULSE】</b>\n"
            + "\n".join(fx_lines) + "\n"
        )

        text = (
            f"📈 <b>SPARK ONE • Global Markets & Cross-Asset Radar</b>\n"
            f"🕒 <i>Live Update | Time: {now_str}</i>\n\n"
            f"{indices_section}\n"
            f"{stocks_section}\n"
            f"{comms_section}\n"
            f"{forex_section}\n"
            f"📊 <b>Market Pulse:</b>\n"
            f"Cross-asset capital allocation shows continuous sector rotation across equities, energy, and currency channels. Monitor correlation shifts.\n\n"
            f"#GlobalMarkets #Stocks #Commodities #Forex #Macro #SparkOne"
        )

        return {
            "title": f"Global Markets Radar ({chosen_theme['theme_name']})",
            "type": "global_stocks",
            "quotes": quotes,
            "theme": chosen_theme,
            "picked_stocks": picked_stocks,
            "picked_commodities": [picked_energy, picked_ind_agri],
            "picked_forex": picked_forex,
            "telegram_message": text,
            "generated_at": now_str
        }

    # ================= 业务方法 3: Thread #5 加密资产与综合投研 =================

    @classmethod
    async def get_crypto_pulse_data(cls) -> Dict[str, Any]:
        """
        Thread #5 专属：加密资产流动性雷达
        - 核心锚点：Bitcoin (BTC) + Ethereum (ETH)
        - 轮动抽取：随机挑选 2 个公链/代币 (SOL / BNB / XRP / ADA / DOGE / TRX)
        """
        loop = asyncio.get_event_loop()

        # 抽取 2 种非 BTC/ETH 的代币
        alts = [c for c in cls.CRYPTO_ASSETS if c["id"] not in ("BTC", "ETH")]
        picked_alts = random.sample(alts, 2)

        symbols = ["BTC-USD", "ETH-USD", picked_alts[0]["symbol"], picked_alts[1]["symbol"]]
        quotes = await loop.run_in_executor(None, cls._fetch_quotes_batch_sync, symbols)
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        def fmt_crypto(name, q, role):
            if not q or not q.get("price"):
                return f"• {name}: Synchronizing..."
            icon = "🟢 +" if q["change"] >= 0 else "🔴 "
            return f"• <b>{name}</b>: <b>${q['price']:,}</b> ({icon}{q['change_pct']}%)  <i>↳ {role}</i>"

        text = (
            f"⚡ <b>SPARK AI • Digital Asset Liquidity Pulse</b>\n"
            f"🕒 <i>Updated: {now_str}</i>\n\n"
            f"<b>【CORE ANCHORS】</b>\n"
            f"{fmt_crypto('Bitcoin (BTC)', quotes.get('BTC-USD'), 'Macro store-of-value anchor')}\n"
            f"{fmt_crypto('Ethereum (ETH)', quotes.get('ETH-USD'), 'Smart contract settlement layer')}\n\n"
            f"<b>【ROTATED LAYER-1 & ECOSYSTEM ASSETS】</b>\n"
            f"{fmt_crypto(picked_alts[0]['name'], quotes.get(picked_alts[0]['symbol']), picked_alts[0]['role'])}\n"
            f"{fmt_crypto(picked_alts[1]['name'], quotes.get(picked_alts[1]['symbol']), picked_alts[1]['role'])}\n\n"
            f"🧠 <b>AI Trend & Flow Insight:</b>\n"
            f"On-chain velocity indicators show healthy capital rotation across primary layer-1 protocols. Decentralized liquidity remains orderly.\n\n"
            f"#Crypto #BTC #ETH #{picked_alts[0]['id']} #{picked_alts[1]['id']} #Web3 #SparkAI"
        )

        return {
            "title": f"Crypto Liquidity Pulse ({picked_alts[0]['id']} & {picked_alts[1]['id']} Featured)",
            "quotes": quotes,
            "picked_alts": picked_alts,
            "telegram_message": text,
            "generated_at": now_str
        }

    @classmethod
    async def get_market_intelligence_data(cls) -> Dict[str, Any]:
        """综合多维归因投研简报"""
        gold = await cls.get_gold_market_data()
        stocks = await cls.get_global_stocks_data()
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        text = (
            f"📊 <b>SPARK ONE • Cross-Asset Multi-Factor Intelligence</b>\n"
            f"🕒 <i>Analysis Timestamp: {now_str}</i>\n\n"
            f"<b>【CROSS-ASSET PRICING SYNTHESIS】</b>\n"
            f"• <b>Tokenized Gold (PAXG):</b> <code>{gold.get('quotes', {}).get('PAXG-USD', {}).get('price', '-')} USD</code>\n"
            f"• <b>Traditional Spot Gold:</b> <code>{gold.get('quotes', {}).get('GC=F', {}).get('price', '-')} USD</code>\n"
            f"• <b>On-Chain Spread:</b> <code>{gold.get('premium', '+0.00%')}</code>\n"
            f"• <b>US S&P 500:</b> <code>{stocks.get('quotes', {}).get('^GSPC', {}).get('price', '-')} pts</code>\n"
            f"• <b>Nasdaq 100:</b> <code>{stocks.get('quotes', {}).get('^IXIC', {}).get('price', '-')} pts</code>\n\n"
            f"🔍 <b>Core Factor Deconstruction:</b>\n"
            f"1. <b>Dollar Liquidity:</b> Currencies and commodities reflect ongoing central bank rate recalculations;\n"
            f"2. <b>Real Yield Spread:</b> Physical & tokenized safe-havens maintain low correlation with cyclical equities;\n"
            f"3. <b>Risk Boundary:</b> Algorithmic dynamic hedging is activated across cross-asset portfolios.\n\n"
            f"#MarketIntelligence #QuantitativeAnalysis #Macro #SparkOne"
        )

        return {
            "title": "Cross-Asset Multi-Factor Intelligence",
            "type": "market_intelligence",
            "telegram_message": text,
            "generated_at": now_str
        }
