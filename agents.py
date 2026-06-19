# ── Imported Libraries ────────────────────────────────────────────────
from crewai import Agent
from textwrap import dedent
from langchain_openai import ChatOpenAI

# ── Custom Functions (Tools) ──────────────────────────────────────────

###########
# BINANCE #
###########
#from tools.Binance_price_data_tool import sui_price_data_tool as binance_sui_tool  # old version
from tools.Binance_price_data_tool import SuiPriceDataTool #new version with BaseTool class, added at 20/5
binance_sui_tool = SuiPriceDataTool()


####################
# SEARCH & SCRAPER #
####################
# from tools.Search_n_Scraper_tool import (
#     SearchInternetTool,
#     ScrapeWebsiteTool
# )
# search_tool = SearchInternetTool()
# scrape_tool = ScrapeWebsiteTool()

from tools.SearchAIO import SearchAndScrapeTool
search_tool = SearchAndScrapeTool()
########
# DUNE #
########
from tools.Dune_analytics_onchain_tool import SUIOnChainTool # Dune
dune_tool = SUIOnChainTool()


from tools.Scrapper_tool import ScrapeWebsiteTool
scrapper_tool = ScrapeWebsiteTool()
# class CustomAgents:
#     def __init__(self):
#         self.OpenAIGPT35 = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)

#     def agent_name_1(self):
#         return Agent(
#             role="Define agent 1 role here",
#             backstory=dedent(f"""Define agent 1 backstory here"""),
#             goal=dedent(f"""Define agent 1 goal here"""),
#             tools=[search_tool.search_internet],
#             # tools=[search_tool.search_internet, tool_2],
#             allow_delegation=False,
#             verbose=True,
#             llm=self.OpenAIGPT35,
#         )


from crewai import LLM # Added at 20/5

# LOW Haiku (2 Agents)~$0.01 - $0.03 (LOW fidelity is roughly 10-20x cheaper per run — which is exactly the point of having two modes)
# HIGH Sonnet (6 Agents)~$0.15 - $0.40
# #7th agentSonnet (1 Agent)~$0.03 - $0.08

class SuiAgents:
    def __init__(self):
        #self.OpenAIGPT35 = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7) # Compatoble ONLY WITH OLDER VERSIONS FO CREWAI
        self.OpenAIGPT35 = LLM(model="gpt-3.5-turbo")  # Added at 20/5

        # ── HIGH fidelity LLM ────────────────────────────────────
        # You could evene create multiple LLM instances with different settings for different agents if you wanted to get really fancy — 
        # e.g. more creative for the news analyst, more focused for the risk assessor, etc. YOU CAN EVEN SET THE TOKENS MAX SO YOU DON'T HAVE TO WORRY ABOUT 
        # TRUNCATION FOR THE MORE COMPLEX AGENTS.
        # But for simplicity we're using one high-fidelity LLM for all 6 agents in HIGH mode.
        self.llm_high = LLM(
            model="gpt-4o",

            temperature=0.2,
            # LOW temperature for trading — you want consistent, logical reasoning not creative variation.
            # 0.2 gives slight flexibility so agents don't get tuck but stays deterministic enough to trust.
            # Never use 0.7+ for financial analysis.

            max_tokens=4000,
            # Your JSON output is complex (scores, trade params, invalidation conditions etc). 4000 gives headroom.
            # Too low = truncated JSON = parse failure.

            timeout=120, # CrewAI agents can take time especially with tool calls. 120s prevents premature failures.

            top_p=0.85, # Slightly restricted nucleus sampling. Keeps outputs focused on high-probability tokens which matters for numeric precision.

            frequency_penalty=0.1, # Mild penalty prevents agents repeating the same phrases across sections of their output.

            presence_penalty=0.0, # Keep at 0 — presence penalty can push agents away from important financial terms they need to repeat (e.g. "stop loss", "entry range").

            # DO NOT set response_format={"type": "json"} here
            # CrewAI handles this via task expected_output.
            # Setting it at LLM level can conflict with  CrewAI's own prompting.
        )

        # ── LOW fidelity LLM ─────────────────────────────────────
        self.llm_low = LLM(
            model="gpt-4o-mini", # gpt-4o-mini is 20x cheaper than gpt-4o, ~3x faster.  Perfect for LOW fidelity — only 2 agents, Binance data only, quick directional signal.
            temperature=0.1, # Even lower for LOW fidelity — fewer agents means less cross-validation so you want higher determinism to compensate.
            max_tokens=2000, # LOW fidelity output is simpler — 2 agents, less context to synthesize. 2000 is enough and keeps cost down.
            timeout=60, # gpt-4o-mini is fast — 60s is more than enough.
            top_p=0.85,
            frequency_penalty=0.1,
            presence_penalty=0.0,
        )

        # ── 7th agent LLM ────────────────────────────────────────
        self.llm_script = LLM(
            model="gpt-4o", # Script generation needs good instruction following and precise formatting — use gpt-4o.

            temperature=0.3,
            # Slightly higher than analysis agents — the script agent needs to write clear prose (Section 1, 2, 4)
            # alongside structured content. 0.3 allows natural language while staying precise on numbers.

            max_tokens=3000, # Four sections of output — needs enough headroom for the full script without truncation.
            timeout=90,
            top_p=0.9,
            frequency_penalty=0.15, # Slightly higher — prevents repetitive phrasing across the four sections of the script.
            presence_penalty=0.0,
        )




    # ── Agents 1-4 (run in parallel) ─────────────────────────
    # Agent_1
    def crypto_news_analyst(self, fidelity: str):
        return Agent(
            role="Crypto News & Sentiment Analyst",
            backstory=dedent(f"""Ex-journalist turned crypto researcher with 
                             6 years tracking crypto markets. Tracks 
                            500+ sources including Twitter/X, Reddit, Telegram, 
                            and major crypto outlets. Expert at separating signal 
                            from hype."""),
            goal=dedent(f"""Scan and summarize the latest news, announcements, 
                        social media sentiment, and developer activity around SUI. Flag 
                        any catalysts (partnerships, exploits, listings, 
                        regulatory news) that could move the price. Classify overall 
                        sentiment as BULLISH, BEARISH, or NEUTRAL with clear evidence."""),
            tools=[search_tool], #PAID
            allow_delegation=False,
            #max_iter=5, # Limits the maximum number of iterations for a task
            verbose=False,
            #llm=self.OpenAIGPT35,
            llm=self.llm_high,
        )
    


    # Agent_2
    def onchain_data_analyst(self, fidelity: str):
        return Agent(
            role="On-Chain Data Analyst",
            backstory=dedent(f"""Former blockchain engineer turned on-chain analyst. 
                            Spent 4 years building dashboards for DeFi protocols.
                            Expert in Dune Analytics and on-chain pattern recognition.
                            Trusted for spotting whale distribution before price moves."""),
            goal=dedent(f"""Analyze SUI blockchain metrics including active wallets, 
                        transaction volume, TVL, staking rates, and whale movements to assess 
                        whether network fundamentals support a price move. Deliver a STRONG, 
                        NEUTRAL, or WEAK network health verdict."""),
            tools=[dune_tool], # PAID
            allow_delegation=False,
            verbose=False,
            llm=self.llm_high,
        )


    
    # Agent_3
    def technical_analysis_expert(self, fidelity: str):
        return Agent(
            role="Technical Analysis Expert",
            backstory=dedent(f"""Trained as a quant trader at a prop firm. 
                            Specializes in crypto technical analysis. Proficient 
                            in Elliott Wave, Fibonacci retracements, volume 
                            profile, and momentum indicators (RSI, MACD, BB)."""),
            goal=dedent(f"""Analyze SUI price charts across across 7, 30, and 90 day 
                        timeframes. Identify trend direction, key support/resistance 
                        levels, and compute RSI, MACD, and Bollinger Bands and 
                        high-probability entry and exit points. Deliver a BULLISH, 
                        BEARISH, or NEUTRAL technical verdict with specific price levels."""),
            tools = [binance_sui_tool], # FREE
            allow_delegation=False,
            verbose=False,
            llm=self.llm_high,
        )
    
    # Agent_4
    def market_context_expert(self, fidelity: str):
        return Agent(
            role="Macro & Market Context Expert",
            backstory=dedent(f"""Former macro economist who pivoted to crypto in 
                            2019. Deep understanding of  how traditional markets bleed into 
                            crypto cycles. Tracks Fed decisions, CPI data, DXY, and BTC correlation 
                             daily. Known for calling macro turning points early."""),
            goal=dedent(f"""Assess the broader crypto market conditions  and macro-economic 
                        factors affecting Sui. Evaluate BTC dominance, altcoin season index, Fed 
                        policy, risk-on/off sentiment and market liquidity that could affect SUI's 
                        price regardless of its own fundamentals. Deliver a TAILWIND, HEADWIND, or 
                        NEUTRAL verdict for taking a Sui position."""),
            tools=[search_tool], # PAID
            allow_delegation=False,
            verbose=False,
            llm=self.llm_high,
        ) 
    # ── Agent 5 (synthesizer) ─────────────────────────────────
    def risk_assessment_expert(self, fidelity: str):
        return Agent(
            role="Risk Assessment & Synthesis Expert",
            backstory=dedent(f"""Background in risk management at a crypto hedge 
                            fund. Expert at synthesizing conflicting signals into 
                            actionable risk-adjusted recommendations. Believes no 
                            trade is worth taking without a clearly defined exit 
                            on both sides."""),
            goal=dedent(f"""Read ALL four expert reports and synthesize them into a single 
                            coherent risk-adjusted view. Quantify downside risk, compute 
                            risk/reward ratio, suggest stop-loss and take-profit levels, and 
                            produce a preliminary BUY/SELL/HOLD recommendation with position 
                            sizing for conservative, medium, and aggressive risk profiles."""),
            tools=[],
            allow_delegation=False,
            verbose=False,
            llm=self.llm_high,
        ) 
    


    # ── Agent 6 (reviewer/captain) ────────────────────────────
    def crypto_portfolio_manager(self, fidelity: str):
        return Agent(
            role="Senior Crypto Portfolio Manager",
            backstory=dedent(f"""15 years in quantitative finance, last 6 focused 
                on crypto. Managed a $50M altcoin portfolio. Known for 
                cutting through noise and making decisive, data-backed 
                calls under pressure. Known for ruthless quality control — 
                will never approve a recommendation built on shaky data. Has seen every 
                type of analyst mistake and knows exactly what to look for."""),
            goal=dedent(f"""Synthesize all expert reports into a single, confident
                buy/sell/hold recommendation with a risk-adjusted 
                rationale and suggested position size."""),
            tools=[],
            allow_delegation=False,
            verbose=False,
            llm=self.llm_high,
        ) 
    

    # ── Create=or of the move script for pushing transactrion to Blockchain ────────────────────────────
    def move_script_writer(self):
        return Agent(
            role="Sui Move Script Developer",
            backstory="""You are an expert in Sui blockchain trading and the Cetus DEX. 
            You write clear, step-by-step trade execution instructions and Sui CLI commands 
            that a trader can copy and paste to execute a trade manually. You always include 
            exact amounts, addresses, and commands. You never guess — if a value is unknown 
            you clearly mark it as a placeholder the user must fill in.""",
            goal="""Generate a precise, human-readable trade execution script 
            for Sui blockchain based on the trading recommendation provided.""",
            tools=[],  # or add code execution tools
            allow_delegation=False,
            verbose=False,
            llm=self.llm_high,
        )
    

    # ── LOW FIDELITY MODEL AGENTS (3 Agents) ────────────────────────────
    #from tools.Scrapper_tool import ScrapeWebsiteTool
    #scrapper_tool = ScrapeWebsiteTool()

    # Agent_1
    def crypto_market_analyzer_low(self, fidelity: str):
        return Agent(
            role="Crypto Market Analyzer",
            backstory=dedent(f"""You are a fast, focused market data collector. 
                            You scrape public crypto data pages and extract the most 
                            relevant metrics and sentiment signals for SUI. You work 
                            quickly and report only what you find — no guessing."""),
            goal=dedent(f"""Scrape and analyze current SUI market data from 
                        fixed public URLs. Extract price, volume, market cap, 
                        sentiment, and any notable news or events."""),
            tools=[scrapper_tool],
            allow_delegation=False,
            #max_iter=5, # Limits the maximum number of iterations for a task
            verbose=False,
            #llm=self.OpenAIGPT35,
            llm=self.llm_low,
        )
    

    # Agent_3
    def technical_analysis_expert_low(self, fidelity: str):
        return Agent(
            role="Technical Analysis Expert",
            backstory=dedent(f"""Trained as a quant trader at a prop firm. 
                            Specializes in crypto technical analysis. Proficient 
                            in Elliott Wave, Fibonacci retracements, volume 
                            profile, and momentum indicators (RSI, MACD, BB)."""),
            goal=dedent(f"""Analyze SUI price charts across across 7, 30, and 90 day 
                        timeframes. Identify trend direction, key support/resistance 
                        levels, and compute RSI, MACD, and Bollinger Bands and 
                        high-probability entry and exit points. Deliver a BULLISH, 
                        BEARISH, or NEUTRAL technical verdict with specific price levels."""),
            tools = [binance_sui_tool],
            allow_delegation=False,
            verbose=False,
            llm=self.llm_low,
        )
    

    # ── Agent 5 (synthesizer) ─────────────────────────────────
    def risk_assessment_expert_low(self, fidelity: str):
        return Agent(
            role="Risk Assessment & Synthesis Expert",
            backstory=dedent(f"""Background in risk management at a crypto hedge 
                            fund. Expert at synthesizing conflicting signals into 
                            actionable risk-adjusted recommendations. Believes no 
                            trade is worth taking without a clearly defined exit 
                            on both sides."""),
            goal=dedent(f"""Read ALL four expert reports and synthesize them into a single 
                            coherent risk-adjusted view. Quantify downside risk, compute 
                            risk/reward ratio, suggest stop-loss and take-profit levels, and 
                            produce a preliminary BUY/SELL/HOLD recommendation with position 
                            sizing for conservative, medium, and aggressive risk profiles."""),
            tools=[],
            allow_delegation=False,
            verbose=False,
            llm=self.llm_low,
        ) 
    


    # ── Agent 6 (reviewer/captain) ────────────────────────────
    def crypto_portfolio_manager_low(self, fidelity: str):
        return Agent(
            role="Senior Crypto Portfolio Manager",
            backstory=dedent(f"""15 years in quantitative finance, last 6 focused 
                on crypto. Managed a $50M altcoin portfolio. Known for 
                cutting through noise and making decisive, data-backed 
                calls under pressure. Known for ruthless quality control — 
                will never approve a recommendation built on shaky data. Has seen every 
                type of analyst mistake and knows exactly what to look for."""),
            goal=dedent(f"""Synthesize all expert reports into a single, confident
                buy/sell/hold recommendation with a risk-adjusted 
                rationale and suggested position size."""),
            tools=[],
            allow_delegation=False,
            verbose=False,
            llm=self.llm_low,
        ) 
