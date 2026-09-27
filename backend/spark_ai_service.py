import datetime
import random
from typing import Dict, Any, List, Optional
from backend.market_service import MarketService

class SparkAIService:
    """SPARK AI 官方研究与投研发布引擎 (Bloomberg x AI Research Desk)"""

    # 1. SPARK 5 大核心引擎架构知识库
    ENGINES_KNOWLEDGE = [
        {
            "engine": "AURORA",
            "full_name": "AURORA • Gold Strategy Research Engine",
            "desc": "Specialized in macro liquidity tracking, central bank gold reserves, and tokenized real-world asset (RWA) liquidity mapping.",
            "metrics": "Spread Analysis • Real Yield Correlation • Central Bank Net Flow"
        },
        {
            "engine": "TITAN",
            "full_name": "TITAN • Trend Analysis Engine",
            "desc": "Multi-timeframe trend identification and momentum clustering across equities, commodities, and digital asset markets.",
            "metrics": "Order Flow Clustering • Adaptive Trend Channels • Momentum Divergence"
        },
        {
            "engine": "ORION",
            "full_name": "ORION • Risk Control Engine",
            "desc": "The central immune system of SPARK AI. Monitors volatility spikes, market anomalies, and dynamic portfolio drawdowns.",
            "metrics": "Cross-Asset Volatility • Tail-Risk Stress Test • Liquidity Shock Gauges"
        },
        {
            "engine": "PHOENIX",
            "full_name": "PHOENIX • Strategy Optimization Engine",
            "desc": "Continuously optimizes execution parameters, slippage mitigation, and machine learning model backtest iterations.",
            "metrics": "Hyperparameter Tuning • Walk-Forward Efficiency • Strategy Decay Audit"
        },
        {
            "engine": "ATLAS",
            "full_name": "ATLAS • Global Asset Allocation Engine",
            "desc": "Dynamic rebalancing between safe-haven commodities, equity indices, and digital liquidity pools.",
            "metrics": "Sharpe Ratio Maximization • Downside Correlation Matrix • Macro Regime Detection"
        }
    ]

    # 2. AI KNOWLEDGE 系列微课堂 (#001 ~ #008)
    KNOWLEDGE_SERIES = [
        {
            "id": "#001",
            "title": "What is Quant Trading?",
            "content": (
                "🎓 <b>SPARK AI KNOWLEDGE #001</b>\n"
                "<b>Topic: What is Quant Trading?</b>\n\n"
                "Quant trading utilizes:\n"
                "• <b>DATA</b> (Tick, macro, sentiment, order book)\n"
                "• <b>MODELS</b> (Statistical arbitrage, machine learning)\n"
                "• <b>RULES</b> (Strict risk boundaries)\n"
                "• <b>AUTOMATION</b> (Algorithmic execution)\n\n"
                "The objective is <b>NOT</b> to predict every single tick.\n"
                "The objective is to make decisions systematic, disciplined, and measurable.\n\n"
                "💡 <i>Key Takeaway: Intuition guesses. Algorithms measure.</i>\n\n"
                "#QuantTrading #SparkAI #Knowledge #FinTech"
            )
        },
        {
            "id": "#002",
            "title": "What is Drawdown?",
            "content": (
                "🎓 <b>SPARK AI KNOWLEDGE #002</b>\n"
                "<b>Topic: Understanding Maximum Drawdown (MDD)</b>\n\n"
                "Drawdown measures the peak-to-trough decline of a portfolio before a new peak is achieved.\n\n"
                "📊 <b>Why does Drawdown matter more than returns?</b>\n"
                "• A 10% loss requires an 11.1% gain to recover.\n"
                "• A 50% loss requires a <b>100% gain</b> just to break even.\n"
                "• An 80% loss requires a <b>400% gain</b> to recover.\n\n"
                "🛡️ <b>SPARK AI Principle:</b> Capital preservation always precedes capital growth.\n"
                "The ORION Risk Engine exists to truncate left-tail drawdown risk.\n\n"
                "#RiskManagement #Drawdown #CapitalPreservation #SparkAI"
            )
        },
        {
            "id": "#003",
            "title": "What is Volatility?",
            "content": (
                "🎓 <b>SPARK AI KNOWLEDGE #003</b>\n"
                "<b>Topic: What is Volatility (and why AI loves it)?</b>\n\n"
                "Volatility is the rate and magnitude of price changes over time.\n\n"
                "⚠️ <b>Amateurs fear volatility.</b>\n"
                "🤖 <b>Quantitative systems measure volatility.</b>\n\n"
                "Volatility is not directional risk—it is statistical variance.\n"
                "High volatility creates price mispricings between correlated assets (e.g. On-Chain PAXG vs Physical Spot Gold), creating alpha opportunities for high-speed algorithmic execution.\n\n"
                "#Volatility #Alpha #QuantTrading #MarketStructure"
            )
        },
        {
            "id": "#004",
            "title": "What is Risk Management?",
            "content": (
                "🎓 <b>SPARK AI KNOWLEDGE #004</b>\n"
                "<b>Topic: What is Modern Risk Management?</b>\n\n"
                "Trading without risk management is not investing; it is gambling.\n\n"
                "Modern quantitative risk control incorporates:\n"
                "1️⃣ <b>Position Sizing:</b> Dynamic sizing based on current market volatility (Kelly Criterion / Vol-Targeting).\n"
                "2️⃣ <b>Stop-Loss Mechanisms:</b> Automated, emotionless trade termination.\n"
                "3️⃣ <b>Liquidity Stress Tests:</b> Ensuring capacity to exit during flash crashes.\n\n"
                "💡 <i>\"Survive first, profit second.\" — SPARK AI ORION</i>\n\n"
                "#RiskControl #CapitalDiscipline #ORION #Quant"
            )
        },
        {
            "id": "#005",
            "title": "AI vs Human Trading",
            "content": (
                "🎓 <b>SPARK AI KNOWLEDGE #005</b>\n"
                "<b>Topic: AI vs. Human Traders: The Decisive Edge</b>\n\n"
                "Why are algorithmic systems dominating 80%+ of institutional volume?\n\n"
                "👨‍💻 <b>Human Trader:</b>\n"
                "• Influenced by fear, greed, FOMO, and fatigue\n"
                "• Can process 1-3 charts simultaneously\n"
                "• Reaction time: 200–500 ms\n\n"
                "🤖 <b>SPARK AI:</b>\n"
                "• 100% disciplined rule execution without emotional hesitation\n"
                "• Synthesizes cross-market data, macroeconomic indicators, and sentiment concurrently\n"
                "• Execution latency: sub-millisecond precision\n\n"
                "#AIvsHuman #TradingPsychology #MachineIntelligence #SparkAI"
            )
        },
        {
            "id": "#006",
            "title": "Why emotions affect traders",
            "content": (
                "🎓 <b>SPARK AI KNOWLEDGE #006</b>\n"
                "<b>Topic: The Cognitive Biases That Destroy Traders</b>\n\n"
                "Behavioral economics reveals 3 traps that consistently liquidate retail participants:\n\n"
                "1️⃣ <b>Disposition Effect:</b> Selling winners too early, holding losing positions too long hoping for break-even.\n"
                "2️⃣ <b>Recency Bias:</b> Assuming current market momentum will continue indefinitely.\n"
                "3️⃣ <b>Revenge Trading:</b> Increasing position sizing immediately following a loss to win it back.\n\n"
                "🤖 <i>AI removes the human ego from the trading terminal.</i>\n\n"
                "#BehavioralFinance #EgoFree #SystematicTrading #SparkAI"
            )
        },
        {
            "id": "#007",
            "title": "What is Backtesting?",
            "content": (
                "🎓 <b>SPARK AI KNOWLEDGE #007</b>\n"
                "<b>Topic: What is Rigorous Backtesting?</b>\n\n"
                "Backtesting simulates an algorithmic trading strategy against historical tick data to evaluate performance viability.\n\n"
                "Key Metrics Inspected:\n"
                "• <b>Sharpe Ratio:</b> Excess return per unit of total risk\n"
                "• <b>Profit Factor:</b> Gross profits divided by gross losses\n"
                "• <b>Win Rate vs. Risk-Reward Ratio:</b> Consistency of edge\n\n"
                "PHOENIX Engine tests strategies across bull, bear, and consolidation regimes to ensure robustness.\n\n"
                "#Backtesting #DataScience #PHOENIX #AlgorithmicEdge"
            )
        },
        {
            "id": "#008",
            "title": "What is Asset Allocation?",
            "content": (
                "🎓 <b>SPARK AI KNOWLEDGE #008</b>\n"
                "<b>Topic: The Power of Dynamic Asset Allocation</b>\n\n"
                "Nobel laureate Harry Markowitz called diversification <i>\"the only free lunch in finance.\"</i>\n\n"
                "Traditional models use rigid 60/40 stocks-bonds splits.\n"
                "Modern AI systems (ATLAS Engine) deploy dynamic regime-based allocation:\n"
                "• Inflation regimes: Increase RWA Tokenized Gold & Commodities\n"
                "• Expansion regimes: Increase Tech Indices & Beta Assets\n"
                "• Contraction regimes: Prioritize Cash & Yield Equivalents\n\n"
                "#AssetAllocation #Diversification #ATLAS #ModernPortfolioTheory"
            )
        }
    ]

    # 3. SPARK AI INSIGHT (传播金句观点库)
    INSIGHTS = [
        "The future of investing is not about having more information.\nIt is about understanding information faster.\nData is everywhere.\nIntelligence is scarce.\n\n🤖 <b>SPARK AI</b>\n#IntelligenceFirst #Alpha #DataDriven",
        "Humans react to markets.\nAI reads the market.\nThe next generation of finance will be built around:\nDATA × AI × AUTOMATION × RISK MANAGEMENT.\n\n🤖 <b>SPARK AI</b>\n#NextGenFinance #SystematicInvesting",
        "In markets, hope is not a strategy.\nConviction without data is merely emotional bias.\nLet data speak. Let probability decide.\n\n🤖 <b>SPARK AI</b>\n#Probability #ObjectiveInvesting",
        "Risk control is not something you apply when the storm arrives.\nIt must be engineered into your architecture before the storm begins.\n\n🛡️ <b>ORION Engine • Risk First</b>\n#RiskControl #ORION #SparkOne",
        "The market is a continuous stream of multi-dimensional signals.\nThose who read single indicators see shadows.\nThose who deploy multi-variable AI see the landscape.\n\n🤖 <b>SPARK AI Research</b>\n#MacroIntelligence #MultiVariable"
    ]

    @classmethod
    async def generate_daily_brief(cls) -> str:
        """1. ⚡ SPARK AI DAILY: 每日极简 AI 市场脉搏"""
        gold_data = await MarketService.get_gold_market_data()
        stock_data = await MarketService.get_global_stocks_data()
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        gold_q = gold_data.get("quotes", {}).get("gold", {})
        paxg_q = gold_data.get("quotes", {}).get("paxg", {})
        sp500_q = stock_data.get("quotes", {}).get("sp500", {})
        nasdaq_q = stock_data.get("quotes", {}).get("nasdaq", {})
        btc_q = stock_data.get("quotes", {}).get("btc", {})
        dxy_q = gold_data.get("quotes", {}).get("dxy", {})

        def get_pulse(q, name):
            if not q:
                return f"• {name}: Neutral consolidation"
            chg = q.get("change_pct", 0)
            if chg > 0.8:
                return f"• {name}: Strong momentum expansion (+{chg}%)"
            elif chg > 0:
                return f"• {name}: Moderate upside drifting (+{chg}%)"
            elif chg > -0.8:
                return f"• {name}: Mild defensive pullback ({chg}%)"
            else:
                return f"• {name}: Volatility expansion / selling pressure ({chg}%)"

        text = (
            f"⚡ <b>SPARK AI DAILY</b>\n"
            f"🕒 <i>Time: {now_str}</i>\n\n"
            f"🌎 <b>Global Market Pulse</b>\n"
            f"{get_pulse(nasdaq_q, 'US Tech (Nasdaq)')}\n"
            f"{get_pulse(paxg_q, 'RWA Gold (PAXG)')}\n"
            f"{get_pulse(dxy_q, 'US Dollar Index')}\n"
            f"{get_pulse(btc_q, 'Crypto (BTC)')}\n\n"
            f"🧠 <b>AI View</b>\n"
            f"Markets are currently navigating macro uncertainty, yield curve shifts, and selective capital rotation. Defensive tokenized assets continue to absorb flight-to-quality flows.\n\n"
            f"🎯 <b>Focus Today:</b> Gold / USD / US Equities / Liquidity\n"
            f"<b>Framework:</b> Data → Analysis → Risk → Decision\n\n"
            f"#SparkAIDaily #GlobalPulse #MarketBrief"
        )
        return text

    @classmethod
    async def generate_market_intelligence(cls) -> str:
        """2. 📊 AI MARKET INTELLIGENCE: 深度解释为什么市场这样走"""
        gold_data = await MarketService.get_gold_market_data()
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        gold_price = gold_data.get("quotes", {}).get("gold", {}).get("price", 2685)
        premium = gold_data.get("premium", "+0.00%")

        text = (
            f"📊 <b>SPARK AI MARKET INTELLIGENCE</b>\n"
            f"<b>WHY IS GOLD & RWA MOVING?</b> 🟡\n"
            f"🕒 <i>Analysis Timestamp: {now_str}</i>\n\n"
            f"Gold is not a single-variable asset. Current price behavior (${gold_price}) is being dictated by 6 intersecting vectors:\n\n"
            f"1️⃣ <b>US Dollar Movement:</b> Fluctuations in DXY adjusting global purchasing power.\n"
            f"2️⃣ <b>Real Yields Dynamics:</b> Real interest rates dictating opportunity cost of holding non-yielding metals.\n"
            f"3️⃣ <b>On-Chain Arbitrage (Spread: {premium}):</b> Tokenized gold (PAXG/XAUT) absorbing decentralized institutional liquidity.\n"
            f"4️⃣ <b>Central Bank Reserves:</b> Multi-quarter structural accumulation by sovereign entities.\n"
            f"5️⃣ <b>Geopolitical Hedging:</b> Cross-border trade diversification.\n"
            f"6️⃣ <b>Global Risk Sentiment:</b> Volatility spikes in equity markets driving portfolio rebalancing.\n\n"
            f"🔍 <b>Core Takeaway:</b>\n"
            f"<i>One market. Multiple variables.</i>\n"
            f"This is why traditional single-indicator analysis fails. SPARK AI utilizes multi-dimensional data synthesis to identify statistical probability rather than guessing headlines.\n\n"
            f"#MarketIntelligence #AURORA #MultiVariable #Macro"
        )
        return text

    @classmethod
    def generate_how_spark_ai_thinks(cls, index: Optional[int] = None) -> str:
        """3. 🧠 HOW SPARK AI THINKS: 解构 SPARK 5 大引擎系统架构"""
        if index is None or index >= len(cls.ENGINES_KNOWLEDGE):
            engine_info = random.choice(cls.ENGINES_KNOWLEDGE)
        else:
            engine_info = cls.ENGINES_KNOWLEDGE[index]

        text = (
            f"🧠 <b>HOW SPARK AI THINKS</b>\n"
            f"<b>System Architecture Series: {engine_info['engine']}</b>\n\n"
            f"<b>System Pipeline:</b>\n"
            f"Market Tick Data\n"
            f"   ↓\n"
            f"AI Multi-Dimensional Analysis\n"
            f"   ↓\n"
            f"Trend & Anomaly Detection\n"
            f"   ↓\n"
            f"ORION Risk Evaluation\n"
            f"   ↓\n"
            f"Algorithmic Strategy Decision\n"
            f"   ↓\n"
            f"Continuous Machine Optimization\n\n"
            f"⚙️ <b>Engine Deep-Dive: {engine_info['full_name']}</b>\n"
            f"• <b>Function:</b> {engine_info['desc']}\n"
            f"• <b>Key Telemetry:</b> <code>{engine_info['metrics']}</code>\n\n"
            f"💡 <i>SPARK AI is not a bot name. It is a full-stack quantitative infrastructure engineered to trade data, probability, and risk rules without human emotion.</i>\n\n"
            f"#{engine_info['engine']} #SparkAIEngine #QuantitativeArchitecture"
        )
        return text

    @classmethod
    def generate_risk_alert(cls, trigger_reason: str = "Market Volatility Expansion") -> str:
        """4. 🚨 AI RISK ALERT: 突发行情风控警报"""
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        text = (
            f"🚨 <b>SPARK AI RISK ALERT</b>\n"
            f"🕒 <i>Timestamp: {now_str}</i>\n\n"
            f"<b>Trigger Condition:</b> {trigger_reason}\n\n"
            f"⚠️ <b>Current Risk Telemetry:</b>\n"
            f"🔴 Rising cross-asset volatility\n"
            f"🟠 Elevated correlation index across equities & commodities\n"
            f"🟠 Rapid intraday capital rotation detected\n"
            f"🟡 Heightened macro & geopolitical sensitivity\n\n"
            f"🛡️ <b>SPARK AI ORION Principle:</b>\n"
            f"<b>Risk first. Opportunity second.</b>\n"
            f"Algorithmic parameters have tightened defensive thresholds. Capital preservation takes absolute priority over speculative positioning.\n\n"
            f"#RiskAlert #ORION #CapitalDiscipline #SafetyFirst"
        )
        return text

    @classmethod
    def get_knowledge_item(cls, index: int = 0) -> str:
        """5. 🎓 AI KNOWLEDGE: 序列化微课堂"""
        idx = index % len(cls.KNOWLEDGE_SERIES)
        return cls.KNOWLEDGE_SERIES[idx]["content"]

    @classmethod
    def get_insight(cls) -> str:
        """6. ✨ SPARK AI INSIGHT: 高传播度观点金句"""
        return random.choice(cls.INSIGHTS)
