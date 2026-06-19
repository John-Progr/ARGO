from crewai import Task
from textwrap import dedent


SUI_URLS = [
    "https://coinmarketcap.com/currencies/sui/",
    "https://www.coingecko.com/en/coins/sui",
    "https://crypto.news/tag/sui/",
    "https://coinmarketcap.com/el/currencies/sui/#News", # good fallback
    "https://coincodex.com/crypto/sui-network/",         # good fallback
    "https://cryptoslate.com/coins/sui/",                # another fallback
]

# class CustomTasks:
#     def __tip_section(self):
#         return "If you do your BEST WORK, I'll give you a $10,000 commission!"

#     def task_1_name(self, agent, var1, var2):
#         return Task(
#             description=dedent(
#                 f"""
#             Do something as part of task 1
            
#             {self.__tip_section()}
    
#             Make sure to use the most recent data as possible.
    
#             Use this variable: {var1}
#             And also this variable: {var2}
#         """
#             ),
#             expected_output="The expected output of the task",
#             agent=agent,
        # )


class SuiTradingTasks:

    def __tip_section(self):
        return "If you do your BEST WORK, I'll give you a $10,000 commission!"

    # ================================================================
    # TASK 1 — News & Sentiment Analyst (async)
    # ================================================================
    def news_and_sentiment_task(self, agent, coin: str = "SUI"):
        return Task(
            description=dedent(
                f"""
                **Task**: Gather and analyze the latest news and sentiment for {coin}.
                **Description**: Search the web for the most recent and relevant news 
                    about {coin} crypto coin in the last 48 hours. This includes:
                    - Major announcements (partnerships, listings, protocol upgrades)
                    - Regulatory news that could impact {coin} or the broader crypto market
                    - Social media sentiment on Twitter/X, Reddit, and Telegram
                    - Developer activity and GitHub commits
                    - Any FUD (fear, uncertainty, doubt) or hype cycles currently in play

                    Scrape and read full articles where needed. Do not rely on headlines alone.
                    Use your tools — do NOT manually summarize without fetching real data.
                    Classify overall sentiment as: BULLISH / BEARISH / NEUTRAL and explain why.

                **Parameters**:
                - Coin: {coin}
                - Timeframe: Last 48 hours only. Ignore older news.
                - Sources to prioritize: CoinDesk, CoinTelegraph, The Block, Twitter/X, Reddit r/sui

                **Note**: {self.__tip_section()}
                """
            ),
            #The "expected_output" works only with newer version of CrewAI. If you are using an older version, please ignore this parameter.
            expected_output=dedent(
                """
                **Expected Output**: 
                    A structured report containing:
                    1. Top 5 most impactful news items with source and date
                    2. Overall sentiment score: BULLISH / BEARISH / NEUTRAL + why
                    3. Key catalysts to watch in the next 24-72 hours
                    4. Any red flags or tail risks identified
                """
            ),
            agent=agent,
            async_execution=True,  # runs in parallel with tasks 2, 3, 4
        )

    # ================================================================
    # TASK 2 — On-Chain Data Analyst (async)
    # ================================================================
    def onchain_analysis_task(self, agent, coin: str = "SUI"):
        return Task(
            description=dedent(
                f"""
                **Task**: Analyze on-chain and market metrics for {coin} to assess network health.
                **Description**: Call the SUI On-Chain Data Tool with input "{coin}".
                    The tool returns live data from the Sui mainnet RPC, DefiLlama, and CoinGecko.
                    You MUST call the tool — do NOT manually estimate any values.

                    Once you have the tool output, evaluate:
                    - Total transaction count: is the network heavily used?
                    - Active validators and total staked SUI: is the network decentralized and secure?
                    - DeFi TVL: is capital flowing in or out of Sui DeFi?
                    - 24h trading volume vs market cap: is liquidity healthy?
                    - 24h and 7d price change: recent momentum direction?

                **Parameters**:
                - Coin: {coin}

                **Note**: {self.__tip_section()}
                """
            ),
            expected_output=dedent(
                """
                **Expected Output**:
                    A structured report containing:
                    1. Each metric value from the tool with a brief interpretation
                    2. Liquidity assessment: is 24h volume healthy relative to market cap?
                    3. Network health verdict: STRONG / NEUTRAL / WEAK with justification
                    4. Any red flags in the on-chain data (low TVL, low staking, price dump)
                """
            ),
            agent=agent,
            async_execution=True,  # runs in parallel with tasks 1, 3, 4
        )

    # ================================================================
    # TASK 3 — Technical Analysis (async)
    # ================================================================
    def technical_analysis_task(self, agent, coin: str = "SUI"):
        return Task(
            description=dedent(
                f"""
                **Task**: Perform technical analysis on {coin} across multiple timeframes.
                **Description**: Use the SUI Price Data Tool to fetch OHLCV data
                    and compute key technical indicators. Call the tool THREE times 
                    with different intervals:

                    - interval: 1h  (short term)
                    - interval: 1d  (medium term)
                    - interval: 1w  (long term — use limit 52 for 1 year of weekly)


                    DO NOT manually estimate prices. Use the tool.

                    Evaluate the following:
                    - Trend direction: is {coin} in an uptrend, downtrend, or ranging?
                    - RSI: overbought (>70), oversold (<30), or neutral?
                    - MACD: bullish or bearish crossover?
                    - Bollinger Bands: is price near upper or lower band?
                    - Key support levels: where will price likely bounce?
                    - Key resistance levels: where will price likely get rejected?
                    - Volume: is the trend confirmed by volume?

                **Parameters**:
                - Coin: {coin}
                - Timeframes: 1h, 1d, 1w



                **Note**: {self.__tip_section()}
                """
            ),
            expected_output=dedent(
                """
                **Expected Output**:
                    A structured report containing:
                    1. Trend summary per timeframe (short / medium / long)
                    2. Key support levels with price values
                    3. Key resistance levels with price values
                    4. Indicator readings: RSI, MACD, Bollinger Bands
                    5. Suggested entry price range and invalidation level
                    6. Technical verdict: BULLISH / BEARISH / NEUTRAL
                """
            ),
            agent=agent,
            async_execution=True,  # runs in parallel with tasks 1, 2, 4
        )

    # ================================================================
    # TASK 4 — Macro & Market Analysis (async)
    # ================================================================
    def macro_analysis_task(self, agent, coin: str = "SUI"):
        return Task(
            description=dedent(
                f"""
                **Task**: Assess macro and broader crypto market conditions affecting {coin}.
                **Description**: Research the current macro-economic environment and 
                    broader crypto market structure to determine if conditions are 
                    favorable for a {coin} position. Evaluate:
                    - Bitcoin trend: is BTC in a bull or bear phase? (altcoins follow BTC)
                    - BTC dominance: rising dominance = bad for altcoins like {coin}
                    - Altcoin season index: are altcoins outperforming BTC right now?
                    - Global crypto market cap: expanding or contracting?
                    - Macro factors: Fed interest rate stance, CPI data, DXY strength
                    - Risk-on vs risk-off: are investors taking on risk or fleeing to safety?
                    - Liquidity conditions: is there money flowing into crypto markets?

                **Parameters**:
                - Coin: {coin}
                - Macro lookback: last 30 days



                **Note**: {self.__tip_section()}
                """
            ),
            expected_output=dedent(
                """
                **Expected Output**:
                    A structured report containing:
                    1. BTC market phase: BULL / BEAR / RANGING
                    2. Altcoin conditions: FAVORABLE / UNFAVORABLE / NEUTRAL for {coin}
                    3. Key macro risks in the next 30 days (Fed meetings, CPI releases etc.)
                    4. Overall market context verdict: TAILWIND / HEADWIND / NEUTRAL
                        for taking a {coin} position right now
                """
            ),
            agent=agent,
            async_execution=True,  # runs in parallel with tasks 1, 2, 3
        )

    # ================================================================
    # TASK 5 — Risk Synthesis (waits for 1-4)
    # ================================================================
    def risk_assessment_task(self, agent, coin: str, context: list):
        return Task(
            description=dedent(
                f"""
                **Task**: Synthesize all four expert reports into a risk-adjusted 
                    preliminary recommendation for {coin}.
                **Description**: You have received four reports:
                    - News & Sentiment report
                    - On-Chain Data report
                    - Technical Analysis report
                    - Macro & Market Context report
                
                    Synthesize them into ONE coherent view. Identify where signals 
                    align (confluence = higher confidence) and where they conflict 
                    (explain how you resolved the conflict).


                    Then produce a risk assessment for a potential {coin} trade:
                    - Volatility: what is {coin}'s average daily % move? 
                    - Liquidity risk: is there enough volume to enter/exit safely?
                    - Downside scenarios: what could go wrong and how bad could it get?
                    - Upside scenarios: what is the realistic best case?
                    - Risk/reward ratio: is the potential gain worth the potential loss?
                    - Suggested stop-loss level: where does the trade idea become invalid?
                    - Suggested take-profit levels: where to take gains?
                    - Maximum position size: what % of a portfolio is safe to allocate?
                    - Tail risks: regulatory crackdown, smart contract exploit, 
                        liquidity crisis, team/project risks specific to {coin}
                    - Position sizing for 3 risk profiles
                    - Top 3 tail risks

                    For each risk identified you MUST provide:
                    - The risk (what it is)
                    - Probability: LOW / MEDIUM / HIGH
                    - Impact if realized: LOW / MEDIUM / HIGH  
                    - Mitigation: what would reduce this risk
                    Vague risk lists without probability/impact score a maximum of 5.
                    
                **Parameters**:
                - Coin: {coin}
                - Risk profiles: conservative / medium / aggressive


                CRITICAL: You MUST provide specific numeric values for ALL trade parameters.
                Current {coin} price is available from the technical analysis context.
                
                For trade_parameters you MUST output:
                - entry_range: specific price range e.g. "$0.85 - $0.90" NOT "around current price"
                - stop_loss: specific price e.g. "$0.79" NOT "below support"
                - take_profit_1: specific price e.g. "$0.95" NOT "at resistance"
                - take_profit_2: specific price e.g. "$1.10" NOT "at major resistance"
                - position_size: specific percentages e.g. "2%" NOT "small"
                
                Use the current price from technical analysis and key levels identified 
                to calculate these. Never use vague descriptions.


                VERY IMPORTANT: The logic of your trade parameters MUST align with THE FOLLOWING trade direction:
                For a BUY trade:
                - You profit when price RISES  
                - Take profits must be ABOVE entry
                - Stop loss must be BELOW entry

                For a SELL trade:
                - You profit when price FALLS
                - Take profits must be BELOW entry (e.g. entry $0.87, TP1 $0.80, TP2 $0.72) - captures profit as price falls
                - Stop loss must be ABOVE entry (e.g. entry $0.87, SL $0.92) - cuts loss if price rises unexpectedly

                Never set a stop loss at the same level as the entry range boundary.


                **Note**: {self.__tip_section()}
                """
            ),
            expected_output=dedent(
                """
                **Expected Output**:
                    A structured report containing:
                    1. Signal alignment summary (where agents agree/disagree)
                    2. Risk/reward ratio (e.g. 1:3)
                    3. Stop-loss price
                    4. Take-profit levels (at least 2)
                    5. Position size per risk profile
                    6. Top 3 tail risks
                    7. Preliminary recommendation: BUY / SELL / HOLD
                    8. Preliminary confidence: LOW / MEDIUM / HIGH / EXTREME

                JSON with ALL trade parameters as specific numeric values.
                entry_range MUST be two dollar amounts e.g. '$0.85 - $0.90'.
                stop_loss MUST be a specific dollar amount e.g. '$0.79'.
                take_profit_1 and take_profit_2 MUST be specific dollar amounts.
                position_size conservative/medium/aggressive MUST be percentages e.g. '2%', '5%', '10%'.
                Vague descriptions like 'around current price' or 'small' are NOT acceptable.
                """
            ),
            agent=agent,
            async_execution=False,  # must wait, not async
        )

    # ================================================================
    # TASK 6 — Final Review with Confidence Scoring / Senior Crypto Portfolio Manager (Captain)
    # ================================================================

    # SAVE TOKENS BY LEAVING THESE RULES OUTSIDE, THEY ARE HARD-CODED IN PYTHON CODE !
    # ═══════════════════════════════════════════════
    # CRITICAL TRADE DIRECTION RULES (NEVER VIOLATE)
    # ═══════════════════════════════════════════════
    # 
    # For {coin}:
    # 
    # BUY TRADE:
    # - TP must be ABOVE entry
    # - SL must be BELOW entry
    # 
    # SELL TRADE:
    # - TP must be BELOW entry
    # - SL must be ABOVE entry
    # 
    # YOU MUST NEVER INVERT THESE RULES.
    def final_review_task(self, agent, coin: str, context: list, fidelity: str = "HIGH"):
        scores_schema = """
            "scores": {
                "news":      {"score": 0-10, "reason": "..."},
                "onchain":   {"score": 0-10, "reason": "..."},
                "technical": {"score": 0-10, "reason": "..."},
                "macro":     {"score": 0-10, "reason": "..."},
                "risk":      {"score": 0-10, "reason": "..."}
            }
        """
        weights_text = "news(15%) + onchain(25%) + technical(30%) + macro(15%) + risk(15%)"
        agents_to_scan = ["news", "onchain", "technical", "macro", "risk"]


        return Task(
            description=dedent(
                f"""
                You are the Senior Crypto Portfolio Manager. Review all agent reports
                and produce a trading verdict for {coin}. Be harsh and skeptical.

                STEP 1 — FAILURE SCAN
                Auto-score 0 if report contains any of:
                "I was unable to find" | "I will manually search" | "lack of available tools" |
                "I couldn't find anything" | "I don't have access" | "as of my knowledge cutoff" |
                "I cannot access real-time"

                STEP 2 — SCORE (0-10)
                10=complete data, 7-9=minor gaps, 4-6=partial, 1-3=mostly assumptions, 0=failed
                Score these agents: {", ".join(agents_to_scan)}

                STEP 3 — CONFIDENCE
                Weights: {weights_text}
                Rules: any 0 → cap at 40 | 2+ zeros → confidence=0, approved=false | <60 → approved=false

                STEP 4 — CROSS-VALIDATE
                Check contradictions, hallucinations, weak assumptions, logic gaps, missing data.
                If any agent scored <7, populate the relevant failure array. Empty arrays with
                sub-7 scores = logic failure.

                STEP 5 — DECISION
                BUY/SELL: clear confluence, confidence>=60
                HOLD: mixed signals, confidence>=60 but no edge
                INSUFFICIENT DATA: only when 2+ agents scored 0
                Score 5 = weak data = HOLD, NOT insufficient data.

                STEP 6 — TRADE PARAMETERS
                Use exact dollar values only. No vague descriptions.
                Derive if missing: SL on BUY=entry-8%, SL on SELL=entry+5%, TP1=±5%, TP2=±10%
                BUY: TPs above entry, SL below. SELL: TPs below entry, SL above.

                STEP 7 — SUI-SPECIFIC PARAMETER RULES:
                Use the ATR (Average True Range) from the technical analysis to derive parameters.

                Boundaries (reject if outside these):
                - Entry range width:  maximum 2% of current price
                - Stop Loss distance: minimum 1%, maximum 5% from entry
                - TP1 distance:       minimum 1%, maximum 5% from entry  
                - TP2 distance:       minimum 2%, maximum 8% from entry
                - Risk/Reward:        TP1 must be at least 1:1 vs SL distance
                                      TP2 must be at least 1:2 vs SL distance

                Derivation method:
                1. Get current ATR from technical analysis
                2. Set SL = 0.8 × ATR from entry
                3. Set TP1 = 1.0 × ATR from entry (1:1 R/R)
                4. Set TP2 = 1.6 × ATR from entry (1:2 R/R minimum)

                If ATR is not available, use 2.5% as default distance.
                Trade horizon: 24-48 hours.
            """
            ),
            expected_output=dedent(
                f"""
                Return ONLY valid JSON. No markdown, no backticks, no explanation text.
                No trailing commas. Every field is required.

                {{
                    "approved": true or false,
                    "overall_confidence": 0-100,
                    {scores_schema},
                    "contradictions":       ["list any contradictions found, or empty array"],
                    "missing_data":         ["list missing signals, or empty array"],
                    "hallucinations":       ["list unsupported claims, or empty array"],
                    "weak_assumptions":     ["list vague claims, or empty array"],
                    "logic_gaps":           ["list reasoning failures, or empty array"],
                    "failed_agents":        ["list of agent names that scored 0, or empty array"],
                    "final_recommendation": "BUY or SELL or HOLD or INSUFFICIENT DATA",
                    "recommendation_confidence": "LOW or MEDIUM or HIGH",
                    "trade_parameters": {{
                        "entry_range":   "$X.XX - $X.XX",
                        "stop_loss":     "$X.XX",
                        "take_profit_1": "$X.XX",
                        "take_profit_2": "$X.XX",
                        "position_size": {{
                            "conservative": "X%",
                            "medium":       "X%",
                            "aggressive":   "X%"
                        }}
                    }},
                    "invalidation_conditions": ["what would make this recommendation wrong"],
                    "reason": "2-3 sentence summary of the key signals driving this verdict"
                }}
                """
            ),
            agent=agent,
            context=context,
            async_execution=False,
        )


    def move_script_task(self, agent, coin: str, amount_usd: float, recommendation: str, trade_parameters: dict):
        action = "SELL" if "SELL" in recommendation.upper() else "BUY"
        entry = trade_parameters.get("entry_range", "N/A")
        stop_loss = trade_parameters.get("stop_loss", "N/A")
        tp1 = trade_parameters.get("take_profit_1", "N/A")
        tp2 = trade_parameters.get("take_profit_2", "N/A")
        pos = trade_parameters.get("position_size", {})

        return Task(
            description=f"""
            Generate a complete trade execution guide for the following recommendation:
            Amount: {amount_usd}
            Coin: {coin}
            Action: {action}
            Entry Range: {entry}
            Stop Loss: {stop_loss}
            Take Profit 1: {tp1}
            Take Profit 2: {tp2}
            Position Sizes:
                Conservative: {pos.get('conservative', 'N/A')}
                Medium: {pos.get('medium', 'N/A')}
                Aggressive: {pos.get('aggressive', 'N/A')}

            You must produce a script with these four sections:

            ---
            SECTION 1 — TRADE SUMMARY
            Plain English summary of what this trade does, why, and the key levels to watch.

            ---
            SECTION 2 — CETUS DEX (Manual UI steps)
            Step by step instructions for executing this trade on https://app.cetus.zone/swap
            Include: which token to swap from/to, amount guidance based on position sizes,
            slippage setting recommendation, and what to check before confirming.

            ---
            SECTION 3 — SUI CLI COMMANDS
            Write the exact Sui CLI commands to execute this trade programmatically.
            Use the following format:

            # Step 1 — Check your balance
            sui client balance

            # Step 2 — Execute swap on Cetus
            sui client call \\
                --package <CETUS_PACKAGE_ID> \\
                --module pool_script \\
                --function swap \\
                --args <POOL_ID> <AMOUNT_IN_MIST> <A_TO_B_BOOL> <MIN_AMOUNT_OUT> \\
                --gas-budget 10000000

            Mark any value the user must fill in with [FILL IN: description].
            Note: 1 SUI = 1,000,000,000 MIST. Include the conversion for the recommended amounts.

            ---
            SECTION 4 — RISK CHECKLIST
            A checklist the user should verify before executing:
            - [ ] Current price is within entry range ({entry})
            - [ ] Stop loss order placed at {stop_loss}
            - [ ] Position size matches your risk tolerance
            - [ ] You have enough SUI for gas (~0.01 SUI)
            - Add any other relevant checks based on the analysis.
            ---

            Be precise. Be actionable. Never hallucinate contract addresses — 
            mark them clearly as [FILL IN] if unknown.


            MANDATORY — copy these EXACTLY into Section 3, do not use placeholders for these:

            For BUY (USDC → SUI):
            sui client call \\
            --package 0x1eabed72c53feb3805120a081dc15963c204dc8d25797af812882d04f8f4dce7 \\
            --module pool_script \\
            --function swap \\
            --args 0xcf994611fd4c48e277ce3ffd4d4364c914af2c3cbb05f7bf6facd371de688630 [FILL IN: YOUR_USDC_AMOUNT] false 0 \\
            --gas-budget 10000000

            For SELL (SUI → USDC):
            sui client call \\
            --package 0x1eabed72c53feb3805120a081dc15963c204dc8d25797af812882d04f8f4dce7 \\
            --module pool_script \\
            --function swap \\
            --args 0xcf994611fd4c48e277ce3ffd4d4364c914af2c3cbb05f7bf6facd371de688630 [FILL IN: AMOUNT_IN_MIST] true 0 \\
            --gas-budget 10000000

            The only [FILL IN] remaining should be the user's actual token amount.
            Show the MIST conversion formula:
            amount_in_mist = YOUR_SUI_BALANCE * POSITION_SIZE_PERCENT * 1,000,000,000
            Example: 100 SUI * 5% = 5 SUI = 5,000,000,000 MIST
            """,
            expected_output="""A complete four-section trade execution guide in plain text, 
            ready to be copied and used by the trader.""",
            agent=agent,
        )
    
    # ── LOW FIDELITY MODEL AGENTS (3 Agents) ────────────────────────────

    # CoinMarketCap and CoinGecko both have bot detection and may block scraping intermittently.
    # As a fallback you can add more reliable plain-text sources:
    # SUI_URLS = [
    #     "https://coinmarketcap.com/currencies/sui/",
    #     "https://www.coingecko.com/en/coins/sui",
    #     "https://crypto.news/tag/sui/",
    #     "https://coinmarketcap.com/el/currencies/sui/#News", # good fallback
    #     "https://coincodex.com/crypto/sui-network/",         # good fallback
    #     "https://cryptoslate.com/coins/sui/",                # another fallback
    # ]

    def market_scrape_task(self, agent, coin: str):
        urls_formatted = "\n".join(f"- {u}" for u in SUI_URLS)

        return Task(
            description=f"""
            Scrape the following URLs and extract key market data for {coin}:

            {urls_formatted}

            From each page extract whatever is available:
            - Current price (USD)
            - 24h price change (%)
            - 24h trading volume
            - Market cap
            - Any recent news headlines or sentiment signals
            - Any notable events (listings, partnerships, upgrades)

            Scrape each URL using the Scrape Website Content tool.
            Combine findings into a single structured report.
            If a URL fails or returns no useful data, note it and move on.
            Do NOT guess or hallucinate values — only report what you find.

            Output format:
            PRICE: $X.XX
            24H CHANGE: X.XX%
            VOLUME: $X
            MARKET CAP: $X
            SENTIMENT: [Bullish / Bearish / Neutral]
            NEWS: [bullet points of any headlines found]
            DATA GAPS: [any URLs that failed or had no useful data]
            """,
            expected_output=f"Structured market data report for Suiscraped from public URLs.",
            agent=agent,
        )
    
    def final_review_task_low(self, agent, coin: str, context: list):
        """LOW fidelity — only technical, market, risk"""
        return Task(
            description=dedent(f"""
                You are reviewing a LOW FIDELITY analysis of {coin}.
                
                ONLY THREE AGENTS RAN. Score ONLY these three:
                1. technical  
                2. market     
                3. risk       

                news, onchain, and macro did NOT run.
                If you output scores for news, onchain, or macro you have failed.

                Confidence weights:
                - technical: 60%
                - market:    25%
                - risk:      15%

                Scoring scale:
                - 10: Complete data, specific numbers, clear conclusion
                - 7-9: Good data, minor gaps
                - 4-6: Partial data, some assumptions
                - 1-3: Mostly assumptions
                - 0: Failed to fetch data or hallucinated

                Confidence rules:
                - If ANY of the three agents scores 0 → cap at 40
                - If 2+ score 0 → overall_confidence = 0, approved = false
                - If overall_confidence < 60 → approved = false

                For {coin} trade direction:
                - SELL: take profits BELOW entry, stop loss ABOVE entry
                - BUY:  take profits ABOVE entry, stop loss BELOW entry

                Trade parameters must be specific dollar values — no vague descriptions.
                If no exact levels provided, derive them:
                - Stop loss BUY:  entry - 8%
                - Stop loss SELL: entry + 5%
                - TP1: entry ± 5%
                - TP2: entry ± 10%

                {self.__tip_section()}
            """),
            expected_output=dedent("""
                Return ONLY valid JSON. No markdown. No backticks. No extra text.
                {
                    "approved": true or false,
                    "overall_confidence": 0-100,
                    "scores": {
                        "technical": {"score": 0-10, "reason": "..."},
                        "market":    {"score": 0-10, "reason": "..."},
                        "risk":      {"score": 0-10, "reason": "..."}
                    },
                    "contradictions":            [],
                    "missing_data":              [],
                    "hallucinations":            [],
                    "weak_assumptions":          [],
                    "logic_gaps":                [],
                    "failed_agents":             [],
                    "final_recommendation":      "BUY or SELL or HOLD or INSUFFICIENT DATA",
                    "recommendation_confidence": "LOW or MEDIUM or HIGH",
                    "trade_parameters": {
                        "entry_range":   "$X.XX - $X.XX",
                        "stop_loss":     "$X.XX",
                        "take_profit_1": "$X.XX",
                        "take_profit_2": "$X.XX",
                        "position_size": {
                            "conservative": "X%",
                            "medium":       "X%",
                            "aggressive":   "X%"
                        }
                    },
                    "invalidation_conditions": ["..."],
                    "reason": "2-3 sentence summary"
                }
            """),
            agent=agent,
            context=context,
            async_execution=False,
        )
