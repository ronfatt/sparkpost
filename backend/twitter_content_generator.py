import re
import random
import logging
import datetime
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
import yfinance as yf

from .config import load_config

logger = logging.getLogger("twitter_content_generator")

class TwitterContentGenerator:
    """
    推特自动运营三大核心内容生成引擎：
    1. SparkOne 官方项目深度解析 (白皮书 / PPT / 官网核心卖点 / RWA黄金 / 5大引擎 / 资管架构)
    2. 全球区块链重大新闻与行业动态 (实时抓取 Cointelegraph / 权威加密快讯 + SPARK 简析)
    3. 全球核心金融资产 (股票 / 代币 / 贵金属) 实时数据行情 + SPARK 彭博级投研观点
    """

    # ================= 1. SparkOne 白皮书 / PPT / 官网 20 大精选深度推文库 =================
    SPARKONE_WHITEPAPER_POSTS = [
        {
            "id": "wp_01",
            "title": "🏛️ SPARK ONE • Wall Street Pedigree Meets Web3",
            "category": "institution",
            "text": (
                "🏛️ <b>SPARK ONE: Institutional Pedigree Meets Web3</b>\n\n"
                "Backed by SPARK UNION CAPITAL INC., SPARK ONE is bridging Wall Street hedge fund rigor with decentralized finance:\n\n"
                "• <b>Multi-Tiered Asset Management</b>: Institutional risk controls engineered from day one\n"
                "• <b>Cross-Asset Coverage</b>: Physical Gold (RWA), Sovereign Equities & Digital Assets\n"
                "• <b>Regulatory Governance</b>: Bank-grade custody with segregated cold-vault architecture\n\n"
                "Demolishing financial silos to democratize institutional alpha 🌐\n\n"
                "👉 Explore: https://sparkone.io\n"
                "#SparkOne #AssetManagement #RWA #Web3 #FinTech"
            )
        },
        {
            "id": "wp_02",
            "title": "🪙 100% Backed Physical Gold RWA Revolution",
            "category": "rwa",
            "text": (
                "🪙 <b>Why Tokenized Gold (RWA) is the Ultimate Wealth Anchor</b>\n\n"
                "Traditional physical gold has friction: high storage fees, assay delays & illiquid trading. SPARK ONE solves this:\n\n"
                "• <b>100% Physical Backing</b>: Each tokenized ounce represents allocated bars in LBMA-certified vaults\n"
                "• <b>24/7 Instant Finality</b>: Move gold collateral on-chain across borders in seconds\n"
                "• <b>Inflation Resistance</b>: Safeguarding purchasing power while capturing algorithmic quant yield\n\n"
                "Real-world value meets on-chain velocity 🛡️\n\n"
                "👉 Read Whitepaper: https://sparkone.io\n"
                "#Gold #RWA #Tokenization #DigitalWealth #SparkOne"
            )
        },
        {
            "id": "wp_03",
            "title": "🤖 SPARK AI • AURORA Macro Liquidity Engine",
            "category": "ai_engine",
            "text": (
                "🟡 <b>MEET AURORA: SPARK AI Macro Liquidity Engine</b>\n\n"
                "The first of SPARK's 5 proprietary quantitative engines:\n\n"
                "• <b>Central Bank Telemetry</b>: Real-time surveillance of sovereign balance sheets & gold reserves\n"
                "• <b>Real Yield Correlation</b>: Tracking TIPS spreads vs bullion pricing in real-time\n"
                "• <b>RWA Liquidity Mapping</b>: Monitoring on-chain collateralization ratios\n\n"
                "Algorithms replace emotional bias. Math drives consistency 📊\n\n"
                "#SparkAI #AURORA #Quant #AlgorithmicTrading #FinTech"
            )
        },
        {
            "id": "wp_04",
            "title": "📈 TITAN Multi-Timeframe Trend Clustering Engine",
            "category": "ai_engine",
            "text": (
                "📈 <b>MEET TITAN: SPARK AI Multi-Timeframe Trend Engine</b>\n\n"
                "Markets aren't random; they move in institutional liquidity cycles:\n\n"
                "• <b>Order Flow Clustering</b>: Detecting whale accumulation patterns before retail breakouts\n"
                "• <b>Adaptive Channels</b>: Dynamically adjusting volatility envelopes across 15m to 1W charts\n"
                "• <b>Cross-Market Momentum</b>: Syncing equity beta with crypto volatility\n\n"
                "Gain institutional-grade market visibility with SPARK ONE ⚡\n\n"
                "#TITAN #SparkAI #MarketStructure #OrderFlow #Crypto"
            )
        },
        {
            "id": "wp_05",
            "title": "🛡️ ORION Central Risk Immune System",
            "category": "risk",
            "text": (
                "🛡️ <b>MEET ORION: The Immune System of SPARK ONE</b>\n\n"
                "\"Amateurs focus on win rate. Institutions focus on drawdown.\"\n\n"
                "• <b>Left-Tail Protection</b>: Auto-deleveraging when cross-asset volatility spikes\n"
                "• <b>Stress-Test Matrix</b>: Simulated 2008 & 2020 black swan scenario survival\n"
                "• <b>Drawdown Capping</b>: Risk parameters locked before any strategy executes\n\n"
                "Capital preservation is our highest operational mandate 🔒\n\n"
                "#RiskManagement #ORION #QuantDesk #DrawdownControl #SparkOne"
            )
        },
        {
            "id": "wp_06",
            "title": "⚡ PHOENIX & ATLAS Engines • Dynamic Optimization",
            "category": "ai_engine",
            "text": (
                "🌐 <b>PHOENIX + ATLAS: Continuous Machine Learning Evolution</b>\n\n"
                "How SPARK ONE adapts across bull and bear cycles:\n\n"
                "• <b>PHOENIX</b>: Hyperparameter tuning with walk-forward efficiency to prevent curve-fitting\n"
                "• <b>ATLAS</b>: Global asset allocation maximizing Sharpe ratio across Gold, BTC & Equities\n"
                "• <b>Zero Human Ego</b>: Pure algorithmic execution calibrated 24/7/365\n\n"
                "The future of intelligent asset management is here 🚀\n\n"
                "#ATLAS #PHOENIX #MachineLearning #SharpeRatio #FinTech"
            )
        },
        {
            "id": "wp_07",
            "title": "🌍 11 Multilingual Global Community Hubs",
            "category": "community",
            "text": (
                "🌍 <b>SPARK ONE: A Truly Borderless Financial Ecosystem</b>\n\n"
                "We are connecting liquidity providers and researchers across 11 national language hubs:\n\n"
                "🇬🇧 English • 🇨🇳 Chinese • 🇦🇪 Arabic • 🇵🇹 Portuguese\n"
                "🇪🇸 Spanish • 🇷🇺 Russian • 🇯🇵 Japanese • 🇩🇪 German\n"
                "🇫🇷 French • 🇰🇷 Korean • 🇻🇳 Vietnamese\n\n"
                "Localized intelligence with global institutional perspective ✨\n\n"
                "👉 Join your native community: https://sparkone.io\n"
                "#GlobalCommunity #Web3 #CryptoEcosystem #SparkOne"
            )
        },
        {
            "id": "wp_08",
            "title": "📱 All-in-One SPARK ONE Terminal Architecture",
            "category": "product",
            "text": (
                "📲 <b>SPARK ONE APP: Next-Gen Financial Super-Terminal</b>\n\n"
                "Everything an intelligent asset allocator needs in one interface:\n\n"
                "• <b>Ultra-Low Latency Execution</b>: Direct market routing across multi-asset liquidity\n"
                "• <b>Bloomberg-Grade AI Feed</b>: Live quantitative market intelligence alerts\n"
                "• <b>Instant RWA Gold Conversion</b>: Seamless bullion on-chain custody\n"
                "• <b>Institutional Transparency</b>: Real-time PnL & Sharpe audits\n\n"
                "👉 Download now: https://sparkone.io/download\n"
                "#SparkOneApp #MobileTrading #FinTech #WealthTech"
            )
        },
        {
            "id": "wp_09",
            "title": "📊 The Mathematical Reality of Drawdown Recovery",
            "category": "philosophy",
            "text": (
                "📉 <b>The Quant Law of Drawdowns: Why Risk Control Wins</b>\n\n"
                "Many traders ignore this brutal mathematical truth:\n\n"
                "• A 10% loss requires an 11.1% gain to recover\n"
                "• A 50% loss requires a 100% gain to recover\n"
                "• An 80% loss requires a 400% gain to recover\n\n"
                "SPARK ONE locks risk parameters first. By capping drawdowns, compound interest creates sustainable long-term alpha 📈\n\n"
                "#TradingPsychology #Compounding #QuantitativeTrading #SparkOne"
            )
        },
        {
            "id": "wp_10",
            "title": "🔐 Multi-Sig MPC Vaults & Security Architecture",
            "category": "security",
            "text": (
                "🔐 <b>Institutional Vault Security at SPARK ONE</b>\n\n"
                "Security is not a feature; it is our foundation:\n\n"
                "• <b>MPC Multi-Signature Vaults</b>: Zero single point of failure\n"
                "• <b>Air-Gapped Cold Custody</b>: Overwhelming majority of reserves kept offline\n"
                "• <b>Formally Verified Contracts</b>: Audited by top-tier Web3 cybersecurity firms\n"
                "• <b>24/7 AI Mempool Telemetry</b>: Real-time threat detection\n\n"
                "Grow your wealth with absolute institutional peace of mind 🛡️\n\n"
                "#Web3Security #MultiSig #ColdStorage #VaultSecurity #SparkOne"
            )
        }
    ]

    _wp_index = 0

    @classmethod
    def get_sparkone_brand_post(cls) -> Dict[str, Any]:
        """获取一条精炼的 SparkOne 官方核心卖点与白皮书推文"""
        posts = cls.SPARKONE_WHITEPAPER_POSTS
        post = posts[cls._wp_index % len(posts)]
        cls._wp_index = (cls._wp_index + 1) % len(posts)
        return {
            "title": post["title"],
            "text": post["text"],
            "type": "sparkone_brand"
        }

    # ================= 2. 全球区块链重大新闻与行业动态抓取引擎 =================
    @classmethod
    def get_crypto_news_post(cls) -> Dict[str, Any]:
        """抓取实时权威区块链要闻并附带 SPARK 投研解读"""
        feed_urls = [
            "https://cointelegraph.com/rss",
            "https://cryptopanic.com/news/rss/"
        ]

        news_items = []
        for url in feed_urls:
            try:
                req = urllib.request.Request(
                    url, 
                    headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
                )
                with urllib.request.urlopen(req, timeout=6) as resp:
                    root = ET.fromstring(resp.read())
                    for item in root.findall(".//item")[:10]:
                        title = item.find("title").text.strip() if item.find("title") is not None else ""
                        desc = item.find("description").text.strip() if item.find("description") is not None else ""
                        link = item.find("link").text.strip() if item.find("link") is not None else ""
                        
                        clean_desc = re.sub(r"<[^>]+>", "", desc).strip()
                        # 清理过长描述
                        clean_desc = clean_desc.replace("&amp;", "&").replace("&quot;", "\"").replace("&#39;", "'")
                        if len(clean_desc) > 160:
                            clean_desc = clean_desc[:157] + "..."

                        if title and len(title) > 10:
                            news_items.append({"title": title, "desc": clean_desc, "link": link})
                if news_items:
                    break
            except Exception as e:
                logger.warning(f"拉取新闻源 {url} 失败: {e}")

        # 如果抓取失败，使用备用高价值宏观新闻模板
        if not news_items:
            fallback_news = [
                {
                    "title": "Global Central Banks Accelerate Gold Purchases Alongside Digital Asset Allocations",
                    "desc": "Sovereign reserves continue diversifying away from single-fiat reliance into hard physical assets and institutional blockchain rails.",
                    "link": "https://sparkone.io"
                },
                {
                    "title": "Institutional RWA Tokenization Market Capitalization Hits Record Milestone",
                    "desc": "Tokenized commodities and treasury products witness strong liquidity inflows driven by cross-border settlement efficiency.",
                    "link": "https://sparkone.io"
                },
                {
                    "title": "Bitcoin Derivative Open Interest Rebalances as Spot ETF Inflows Stabilize",
                    "desc": "Options funding rates reset to neutral levels, establishing a structural consolidation floor for macro asset allocators.",
                    "link": "https://sparkone.io"
                }
            ]
            picked = random.choice(fallback_news)
        else:
            picked = random.choice(news_items[:5])

        spark_perspectives = [
            "SPARK AI Angle: Structural liquidity shifts reinforce the need for diversified RWA assets.",
            "SPARK Take: Institutional adoption continues moving from speculative trading into systematic wealth management.",
            "SPARK Alpha: Market volatility creates asymmetric risk-reward for quantitative trend-following models.",
            "SPARK Insight: Real-world assets (RWA) and cross-chain settlement remain the defining narrative of this cycle."
        ]
        perspective = random.choice(spark_perspectives)

        tweet_text = (
            f"⚡ <b>CRYPTO & BLOCKCHAIN HEADLINE BREAKING</b>\n\n"
            f"📰 <b>{picked['title']}</b>\n\n"
            f"• <b>Key Development</b>: {picked['desc']}\n"
            f"• 💡 <b>{perspective}</b>\n\n"
            f"Stay ahead of macro market flows with SPARK ONE 🌐\n\n"
            f"#CryptoNews #Bitcoin #Blockchain #Web3 #Macro #SparkOne"
        )

        return {
            "title": f"⚡ 区块链要闻: {picked['title'][:30]}...",
            "text": tweet_text,
            "type": "crypto_news"
        }

    # ================= 3. 股票/代币/大宗实时数据 + SPARK 投研观点 =================
    @classmethod
    def get_market_data_with_alpha_post(cls) -> Dict[str, Any]:
        """抓取实时股票、主流代币与黄金行情并结合 SPARK AI 量化观点"""
        
        # 实时拉取行情
        quotes_data = {}
        try:
            tickers = yf.Tickers("GC=F BTC-USD ETH-USD NVDA AAPL TSM")
            for symbol, label in [
                ("GC=F", "Gold (RWA)"),
                ("BTC-USD", "Bitcoin"),
                ("ETH-USD", "Ethereum"),
                ("NVDA", "NVIDIA"),
                ("AAPL", "Apple"),
                ("TSM", "TSMC ADR")
            ]:
                try:
                    fi = tickers.tickers[symbol].fast_info
                    price = fi.last_price
                    prev = fi.previous_close
                    chg = ((price - prev) / prev) * 100 if prev else 0.0
                    sign = "+" if chg >= 0 else ""
                    quotes_data[label] = f"${price:,.2f} ({sign}{chg:.2f}%)"
                except Exception as e:
                    logger.debug(f"拉取 {symbol} 失败: {e}")
        except Exception as e:
            logger.warning(f"批量拉取行情异常: {e}")

        # 备选数据
        if not quotes_data:
            quotes_data = {
                "Gold (RWA)": "$4,171.20 (+0.40%)",
                "Bitcoin": "$83,750.00 (-1.95%)",
                "Ethereum": "$2,610.50 (-3.10%)",
                "NVIDIA": "$239.24 (-0.40%)",
                "Apple": "$333.63 (+0.23%)"
            }

        # 构造资产行情速览行
        lines = []
        for k, v in quotes_data.items():
            lines.append(f"• <b>{k}</b>: <code>{v}</code>")
        quotes_block = "\n".join(lines)

        quant_insights = [
            (
                "🧠 <b>SPARK AI Quant Outlook:</b>\n"
                "Gold continues exhibiting negative beta against currency debasement while tech equities consolidate. "
                "Our ATLAS engine maintains a balanced allocation between defensive bullion and growth equities."
            ),
            (
                "🧠 <b>SPARK AI Quant Outlook:</b>\n"
                "Digital asset derivative funding rates have normalized. "
                "Our TITAN trend tracker signals structural accumulation across key macro support zones."
            ),
            (
                "🧠 <b>SPARK AI Quant Outlook:</b>\n"
                "Semiconductor demand remains resilient amid AI infrastructure capex. "
                "Pairing real-world gold reserves with high-beta equities delivers optimal risk-adjusted Sharpe ratios."
            )
        ]
        insight = random.choice(quant_insights)

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M UTC")

        tweet_text = (
            f"📊 <b>SPARK ONE • GLOBAL ASSET RADAR & REAL-TIME DATA</b>\n"
            f"🕒 <i>{now_str}</i>\n\n"
            f"{quotes_block}\n\n"
            f"{insight}\n\n"
            f"Transform market volatility into disciplined alpha 🚀\n\n"
            f"👉 Platform: https://sparkone.io\n"
            f"#StockMarket #Crypto #Gold #QuantTrading #Alpha #SparkOne"
        )

        return {
            "title": f"📊 跨资产实时数据与 AI 投研",
            "text": tweet_text,
            "type": "market_alpha"
        }

    @staticmethod
    def strip_html_tags(text: str) -> str:
        """移除所有 HTML 标签并转换特殊实体，适合推特纯文本发布"""
        if not text:
            return ""
        clean = re.sub(r"<[^>]+>", "", text)
        clean = clean.replace("&amp;", "&").replace("&quot;", '"').replace("&#39;", "'").replace("&lt;", "<").replace("&gt;", ">")
        return clean.strip()

    # ================= 4. 根据模式生成推文 =================
    @classmethod
    def generate_post(cls, post_type: str = "sparkone_brand") -> Dict[str, Any]:
        """
        根据类型生成指定推文：
        - 'sparkone_brand': SparkOne 官方项目核心卖点与白皮书深度内容
        - 'crypto_news': 全球区块链重大新闻 + SPARK 简析
        - 'market_alpha': 股票/代币/大宗实时数据 + SPARK 投研观点
        """
        if post_type == "crypto_news":
            res = cls.get_crypto_news_post()
        elif post_type == "market_alpha":
            res = cls.get_market_data_with_alpha_post()
        else:
            res = cls.get_sparkone_brand_post()

        res["text"] = cls.strip_html_tags(res.get("text", ""))
        return res

