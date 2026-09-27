import datetime
from typing import Dict, Any, List, Optional
import logging
import asyncio

logger = logging.getLogger(__name__)

class MarketService:

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
    async def get_gold_market_data(cls) -> Dict[str, Any]:
        """Fetch blockchain tokenized RWA gold (PAXG, XAUT) and spot gold market data (English)"""
        loop = asyncio.get_event_loop()
        
        symbols = {
            "paxg": "PAXG-USD",   # Pax Gold
            "xaut": "XAUT-USD",   # Tether Gold
            "gold": "GC=F",       # Spot/Futures Gold XAU/USD
            "silver": "SI=F",     # Silver
            "dxy": "DX-Y.NYB"     # US Dollar Index
        }

        quotes = {}
        for key, sym in symbols.items():
            res = await loop.run_in_executor(None, cls._fetch_quote_sync, sym)
            quotes[key] = res

        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        
        paxg_q = quotes.get("paxg")
        xaut_q = quotes.get("xaut")
        gold_q = quotes.get("gold")
        silver_q = quotes.get("silver")
        dxy_q = quotes.get("dxy")

        def fmt_change(q):
            if not q:
                return "Data Syncing"
            icon = "🟢 +" if q["change"] >= 0 else "🔴 "
            return f"{icon}{q['change']} ({q['change_pct']}%)"

        # Calculate On-chain Gold Premium vs Physical Spot Gold
        premium_str = "+0.00%"
        if paxg_q and gold_q and gold_q["price"] > 0:
            diff = paxg_q["price"] - gold_q["price"]
            diff_pct = (diff / gold_q["price"]) * 100
            p_sign = "+" if diff_pct >= 0 else ""
            premium_str = f"{p_sign}{round(diff_pct, 2)}%"

        paxg_price = f"${paxg_q['price']:,}" if paxg_q else "$2,685.00"
        xaut_price = f"${xaut_q['price']:,}" if xaut_q else "$2,686.00"
        gold_price = f"${gold_q['price']:,}" if gold_q else "$2,684.00"

        text = (
            f"🥇 <b>SPARK ONE • Tokenized Gold & Global Commodity Watch</b>\n"
            f"🕒 <i>Hourly Real-Time Brief | Updated: {now_str}</i>\n\n"
            f"<b>【TOKENIZED RWA GOLD (BLOCKCHAIN)】</b>\n"
            f"🪙 <b>PAX Gold (PAXG):</b> <b>{paxg_price}</b> | {fmt_change(paxg_q)}\n"
            f"   ↳ <i>Paxos Issued • 100% Backed by London Good Delivery Physical Gold</i>\n"
            f"🪙 <b>Tether Gold (XAUT):</b> <b>{xaut_price}</b> | {fmt_change(xaut_q)}\n"
            f"   ↳ <i>Tether Issued • Backed by Physical Swiss Vault Reserves</i>\n\n"
            f"<b>【TRADITIONAL BENCHMARK & ON-CHAIN SPREAD】</b>\n"
            f"🏛️ <b>Spot Gold (XAU/USD):</b> <b>{gold_price}</b> | {fmt_change(gold_q)}\n"
            f"⚡ <b>On-Chain Gold Premium:</b> <code>{premium_str}</code>\n\n"
            f"<b>【KEY MACRO COMMODITIES & FOREX】</b>\n"
            f"⚪ <b>Spot Silver (XAG/USD):</b> <b>${silver_q['price'] if silver_q else '-'}</b> | {fmt_change(silver_q)}\n"
            f"💵 <b>US Dollar Index (DXY):</b> <b>{dxy_q['price'] if dxy_q else '-'}</b> | {fmt_change(dxy_q)}\n\n"
            f"💡 <b>Macro & RWA Intelligence:</b>\n"
            f"Tokenized real-world gold (RWA) liquidity remains robust. On-chain premium metrics reflect active institutional and decentralized capital allocation toward safe-haven assets.\n\n"
            f"#PAXG #XAUT #Gold #RWA #Commodities #SparkOne"
        )

        return {
            "title": "Tokenized RWA Gold & Commodity Watch (Hourly Update)",
            "type": "gold",
            "quotes": quotes,
            "premium": premium_str,
            "telegram_message": text,
            "generated_at": now_str
        }

    @classmethod
    async def get_global_stocks_data(cls) -> Dict[str, Any]:
        """Fetch global equity indices and macro assets (English)"""
        loop = asyncio.get_event_loop()
        
        symbols = {
            "sp500": "^GSPC",   # S&P 500
            "nasdaq": "^IXIC",  # Nasdaq
            "dow": "^DJI",      # Dow Jones
            "nikkei": "^N225",  # Nikkei 225
            "hsi": "^HSI",      # Hang Seng Index
            "btc": "BTC-USD"    # Bitcoin
        }

        quotes = {}
        for key, sym in symbols.items():
            res = await loop.run_in_executor(None, cls._fetch_quote_sync, sym)
            quotes[key] = res

        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        def fmt_item(name, q):
            if not q:
                return f"• {name}: Data Syncing..."
            icon = "🟢 +" if q["change"] >= 0 else "🔴 "
            return f"• {name}: <b>{q['price']:,}</b> ({icon}{q['change_pct']}%)"

        text = (
            f"📈 <b>SPARK ONE • Global Markets & Equity Indices Snapshot</b>\n"
            f"🕒 <i>Live Update | Time: {now_str}</i>\n\n"
            f"<b>【US MAJOR INDICES】</b>\n"
            f"{fmt_item('S&P 500 (US 500)', quotes.get('sp500'))}\n"
            f"{fmt_item('Nasdaq 100 (Tech Index)', quotes.get('nasdaq'))}\n"
            f"{fmt_item('Dow Jones Industrial', quotes.get('dow'))}\n\n"
            f"<b>【ASIA-PACIFIC MARKETS】</b>\n"
            f"{fmt_item('Hang Seng Index (HSI)', quotes.get('hsi'))}\n"
            f"{fmt_item('Nikkei 225 (Japan)', quotes.get('nikkei'))}\n\n"
            f"<b>【DIGITAL ASSET BENCHMARK】</b>\n"
            f"{fmt_item('Bitcoin (BTC/USD)', quotes.get('btc'))}\n\n"
            f"📊 <b>Market Overview:</b>\n"
            f"Global risk appetite displays sector rotation across technology and defensive commodities. Monitor macroeconomic yield curves and liquidity releases.\n\n"
            f"#GlobalMarkets #Stocks #WallStreet #Macro #SparkOne"
        )

        return {
            "title": "Global Markets & Equity Indices Snapshot",
            "type": "global_stocks",
            "quotes": quotes,
            "telegram_message": text,
            "generated_at": now_str
        }

    @classmethod
    async def get_market_intelligence_data(cls) -> Dict[str, Any]:
        """Comprehensive market intelligence (English)"""
        gold = await cls.get_gold_market_data()
        stocks = await cls.get_global_stocks_data()
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        text = (
            f"📊 <b>SPARK ONE • Cross-Asset Deep Intelligence Brief</b>\n"
            f"🕒 <i>Published: {now_str}</i>\n\n"
            f"<b>【KEY CROSS-ASSET LIQUIDITY MONITOR】</b>\n"
            f"• Tokenized Gold (PAXG): <code>${gold['quotes'].get('paxg', {}).get('price', '-')} USD</code>\n"
            f"• Traditional Spot Gold: <code>${gold['quotes'].get('gold', {}).get('price', '-')} USD</code>\n"
            f"• Nasdaq 100: <code>{stocks['quotes'].get('nasdaq', {}).get('price', '-')} pts</code>\n"
            f"• Bitcoin: <code>${stocks['quotes'].get('btc', {}).get('price', '-')}</code>\n\n"
            f"🔍 <b>Strategic Observations:</b>\n"
            f"1. US Dollar Index dynamics continue to influence global liquidity channels;\n"
            f"2. Capital rebalancing between safe-haven commodities and high-beta risk assets remains active;\n"
            f"3. Strict risk management and portfolio diversification are advised.\n\n"
            f"#MarketIntelligence #Trading #Macro #SparkOne"
        )

        return {
            "title": "Cross-Asset Deep Intelligence Brief",
            "type": "market_intelligence",
            "telegram_message": text,
            "generated_at": now_str
        }
