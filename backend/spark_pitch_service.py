import datetime
import random
from typing import Dict, Any, List, Optional
from backend.config import load_config
from backend.telegram_service import TelegramService

class SparkPitchService:
    """
    SPARK ONE 核心卖点与公司优势宣传引擎
    专门向 General 主题与核心社区推送高质感项目价值、资管实力、RWA黄金背书与量化技术壁垒
    """

    PITCH_TEMPLATES = [
        {
            "id": "pitch_pedigree",
            "title": "🏛️ SPARK ONE • 公司资管背景与机构实力",
            "category": "credibility",
            "text": (
                "🏛️ <b>SPARK ONE • Institutional Asset Management Architecture</b>\n\n"
                "<b>Why Leading Investors Choose SPARK ONE:</b>\n\n"
                "• 🏢 <b>Institutional Pedigree</b>: Powered by SPARK UNION CAPITAL INC., combining traditional Wall Street hedge fund methodology with Web3 technological efficiency.\n"
                "• ⚖️ <b>Regulatory Compliance First</b>: Adhering to international asset management governance standards, multi-tiered auditing, and cold-vault capital segregation.\n"
                "• 📊 <b>Cross-Asset Dominance</b>: Seamlessly synthesizing Physical Gold (RWA), Sovereign FX, Equities, and Digital Assets into one intelligent risk-adjusted portfolio.\n"
                "• 🎯 <b>Our Mission</b>: Demolishing financial silos to bring institutional-grade alpha, transparency, and liquidity to global Web3 participants.\n\n"
                "🌐 <b>Official Portal:</b> https://sparkone.io\n\n"
                "#SparkOne #InstitutionalGrade #FinTech #AssetManagement #Web3"
            )
        },
        {
            "id": "pitch_rwa_gold",
            "title": "🪙 100% 实物黄金托底 • RWA 颠覆性优势",
            "category": "rwa",
            "text": (
                "🪙 <b>THE POWER OF RWA • 100% Physical Gold Backing</b>\n\n"
                "In an era of currency devaluation and macroeconomic uncertainty, <b>Gold remains the ultimate store of value</b>. SPARK ONE bridges traditional gold with decentralized finance:\n\n"
                "• 🏛️ <b>100% Physical Vault Backing</b>: Every digital gold unit corresponds directly to allocated, LBMA-certified physical gold bars stored in top-tier global vaults.\n"
                "• ⚡ <b>24/7 Instant Liquidity</b>: Eliminate traditional custodian delays, high assay fees, and settlement friction. Move gold on-chain with instant finality.\n"
                "• 🛡️ <b>Unshakable Inflation Shield</b>: Protect your capital against purchasing power erosion while earning algorithmic quantitative yield.\n"
                "• 🔍 <b>Cryptographic Transparency</b>: On-chain verifiable proof-of-reserves audited by third-party accounting standards.\n\n"
                "💡 <i>Real physical stability meets the speed of blockchain.</i>\n\n"
                "#Gold #RWA #PAXG #XAUT #Tokenization #SparkOne"
            )
        },
        {
            "id": "pitch_5_engines",
            "title": "🤖 SPARK AI • 5大独家自研量化引擎优势",
            "category": "technology",
            "text": (
                "🧠 <b>THE SPARK AI ADVANTAGE • 5 Proprietary Quant Engines</b>\n\n"
                "SPARK AI is not a generic bot — it is an enterprise multi-agent quantitative framework engineered for multi-asset markets:\n\n"
                "🟡 <b>AURORA</b> • Macro Liquidity & Real Yield Correlation Engine\n"
                "📈 <b>TITAN</b> • Multi-Timeframe Trend & Momentum Clustering Engine\n"
                "🛡️ <b>ORION</b> • Central Immune System & Strict Left-Tail Drawdown Guard\n"
                "⚡ <b>PHOENIX</b> • Dynamic Execution & Adaptive Machine Learning Optimization\n"
                "🌐 <b>ATLAS</b> • Global Multi-Asset Sharpe Ratio Rebalancing Engine\n\n"
                "📊 <b>Algorithms eliminate human emotion. Mathematical probability drives sustained growth.</b>\n\n"
                "#SparkAI #QuantitativeTrading #AlgorithmicFinance #ArtificialIntelligence #FinTech"
            )
        },
        {
            "id": "pitch_security",
            "title": "🛡️ 银行级安全架构 • 机构加密金库防护",
            "category": "security",
            "text": (
                "🛡️ <b>SECURITY FIRST • Institutional Asset Safeguards</b>\n\n"
                "At SPARK ONE, <b>capital preservation is our highest operational mandate</b>. Our defense architecture features:\n\n"
                "• 🔐 <b>Multi-Signature Vault Custody</b>: Zero single point of failure. Multi-party computation (MPC) and multi-signature security protocols.\n"
                "• 🧊 <b>Air-Gapped Cold Storage</b>: The overwhelming majority of institutional reserves remain isolated from Internet-connected attack vectors.\n"
                "• 🔍 <b>Continuous Smart Contract Auditing</b>: Rigorous formal verification by premier cybersecurity auditors.\n"
                "• 🚨 <b>24/7 AI-Powered On-Chain Telemetry</b>: Real-time mempool scanning and threat mitigation against anomalous transaction spikes.\n\n"
                "🔒 <i>Trade, stake, and grow with absolute institutional confidence.</i>\n\n"
                "#Security #AssetSafety #ColdVault #MultiSig #SparkOne"
            )
        },
        {
            "id": "pitch_global_matrix",
            "title": "🌍 全球化生态布局 • 11国语言社群矩阵",
            "category": "ecosystem",
            "text": (
                "🌍 <b>SPARK ONE ECOSYSTEM • A Truly Global Financial Network</b>\n\n"
                "SPARK ONE unites investors, liquidity providers, and quantitative researchers across <b>11 dedicated national language hubs</b>:\n\n"
                "🇬🇧 English • 🇨🇳 Chinese • 🇦🇪 Arabic • 🇵🇹 Portuguese\n"
                "🇪🇸 Spanish • 🇷🇺 Russian • 🇯🇵 Japanese • 🇩🇪 German\n"
                "🇫🇷 French • 🇰🇷 Korean • 🇻🇳 Vietnamese\n\n"
                "✨ <b>Community Core Value:</b>\n"
                "• Localized daily research digests in your native language\n"
                "• Direct access to institutional macro intelligence\n"
                "• Active community reward missions and governance rights\n\n"
                "👉 Join your language topic and experience borderless finance!\n\n"
                "#GlobalCommunity #Web3 #Multilingual #DeFi #SparkOne"
            )
        },
        {
            "id": "pitch_quant_philosophy",
            "title": "📈 稳健复利哲学 • 为什么风控永远大于贪婪？",
            "category": "philosophy",
            "text": (
                "📊 <b>SPARK ONE PHILOSOPHY • Discipline Over Emotion, Risk Over Greed</b>\n\n"
                "Amateurs chase peak win rates. <b>Institutions engineer strict drawdown control.</b>\n\n"
                "📉 <b>The Mathematical Law of Drawdowns:</b>\n"
                "• A 10% loss requires an 11.1% gain to recover\n"
                "• A 50% loss requires a <b>100%</b> gain to recover\n"
                "• An 80% loss requires a <b>400%</b> gain to recover\n\n"
                "SPARK ONE's algorithmic architecture locks risk parameters <b>before execution begins</b>. By capping downside risk, mathematical compounding works in your favor across market cycles.\n\n"
                "💡 <i>Consistent alpha is not luck — it is strict mathematical discipline.</i>\n\n"
                "#Compounding #RiskManagement #CapitalPreservation #QuantitativeFinance #SparkOne"
            )
        },
        {
            "id": "pitch_app_terminal",
            "title": "📱 SPARK ONE APP • 下一代一站式全景金融终端",
            "category": "product",
            "text": (
                "📲 <b>SPARK ONE TERMINAL • Your Gateway to Intelligent Wealth</b>\n\n"
                "Experience the next evolution of digital asset management from the palm of your hand:\n\n"
                "⚡ <b>Ultra-Low Latency Execution</b>: Direct market routing across gold, equities, and crypto pools.\n"
                "🤖 <b>Integrated SPARK AI Feed</b>: Real-time quantitative signals, macro trend alerts, and risk assessments.\n"
                "🪙 <b>Seamless RWA Gold Custody</b>: Instant conversion between digital liquidity and physical gold token holdings.\n"
                "📊 <b>Transparent Portfolio Telemetry</b>: Real-time PnL analytics, Sharpe ratio audits, and drawdown metrics.\n\n"
                "👉 Download the official build: https://sparkone.io/download\n\n"
                "#SparkOneApp #FinTech #MobileTrading #WealthTech #SmartInvesting"
            )
        }
    ]

    _current_index = 0

    @classmethod
    def get_all_pitches(cls) -> List[Dict[str, Any]]:
        """获取所有官方卖点宣传文案列表"""
        return cls.PITCH_TEMPLATES

    @classmethod
    def get_pitch_by_id(cls, pitch_id: str) -> Optional[Dict[str, Any]]:
        """根据 ID 获取指定卖点文案"""
        return next((p for p in cls.PITCH_TEMPLATES if p["id"] == pitch_id), None)

    @classmethod
    def get_next_pitch_post(cls) -> Dict[str, Any]:
        """按顺序或循环获取下一条卖点文案（保障每次自动推送轮播不同优势）"""
        idx = cls._current_index % len(cls.PITCH_TEMPLATES)
        cls._current_index = (cls._current_index + 1) % len(cls.PITCH_TEMPLATES)
        return cls.PITCH_TEMPLATES[idx]

    @classmethod
    def get_random_pitch_post(cls) -> Dict[str, Any]:
        """随机获取一条卖点文案"""
        return random.choice(cls.PITCH_TEMPLATES)

    @classmethod
    async def send_pitch_to_general(cls, pitch_id: Optional[str] = None) -> Dict[str, Any]:
        """一键向 General Topic 发送项目核心卖点宣传内容"""
        cfg = load_config()
        token = cfg.get("telegram", {}).get("bot_token")
        chat_id = cfg.get("telegram", {}).get("chat_id")

        if not token or not chat_id:
            return {"success": False, "error": "请先在【话题绑定与配置】中配置 Telegram Bot Token 和群组 Chat ID"}

        # 查找 General Topic 话题
        topics = cfg.get("topics", [])
        general_topic = next((t for t in topics if t["id"] == "general_chat"), None)
        thread_id = general_topic.get("thread_id") if general_topic else None

        pitch = cls.get_pitch_by_id(pitch_id) if pitch_id else cls.get_next_pitch_post()
        if not pitch:
            pitch = cls.get_next_pitch_post()

        res = await TelegramService.send_message(
            token=token,
            chat_id=chat_id,
            text=pitch["text"],
            thread_id=thread_id,
            parse_mode="HTML"
        )
        res["pitch_title"] = pitch["title"]
        return res
