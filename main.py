import json
import os
from datetime import datetime
from unittest import result
#from textwrap import dedent
from dotenv import load_dotenv
from crewai import Crew #, Process
#from crewai.memory import LongTermMemory, ShortTermMemory, EntityMemory
#from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage
import re


load_dotenv()

from agents import SuiAgents
from tasks import SuiTradingTasks


# SEE WHICH LIBRBARIES YOUR CREWAI VERSION CONTAINS
# python -c "from crewai import events; print(dir(events)) # what MODULES are actually available in your version
# python -c "from crewai.events import _LAZY_EVENT_MAPPING; print(list(_LAZY_EVENT_MAPPING.keys())) # The EVENTS module are lazily loaded via _LAZY_EVENT_MAPPING. Check what event CLASSES are actually available




# ── Config ───────────────────────────────────────────────
# How many times a full kickoff should be run until the "CONF_THRESH" is achieved
MAX_RETRIES = 1
CONFIDENCE_THRESHOLD = 60
coin = "SUI"  # hardcoded (State whatever coin you want BUT THE URL ARE FIXED FOR SUI !)



agents = SuiAgents()
tasks = SuiTradingTasks()


#-------- SEE WHISH AGENT/TASK is currenlty executing
from crewai.events import (
    BaseEventListener,
    crewai_event_bus,
    AgentExecutionStartedEvent,
    AgentExecutionCompletedEvent,
    TaskStartedEvent,
    TaskCompletedEvent,
    CrewKickoffStartedEvent,
    CrewKickoffCompletedEvent,
)


class SuiAdvisorListener(BaseEventListener):
    def __init__(self):
        super().__init__()

    def setup_listeners(self, crewai_event_bus):

        @crewai_event_bus.on(CrewKickoffStartedEvent)
        def on_crew_started(source, event):
            print(f"\n{'='*55}")
            print(f"🚀 Crew kickoff started")
            print(f"{'='*55}")

        @crewai_event_bus.on(TaskStartedEvent)
        def on_task_started(source, event):
            print(f"\n⚡ [{event.task.agent.role}] starting...")

        @crewai_event_bus.on(AgentExecutionStartedEvent)
        def on_agent_started(source, event):
            print(f"🔄 [{event.agent.role}] executing...")

        @crewai_event_bus.on(AgentExecutionCompletedEvent)
        def on_agent_done(source, event):
            print(f"✅ [{event.agent.role}] done")

        @crewai_event_bus.on(TaskCompletedEvent)
        def on_task_done(source, event):
            print(f"🟢 [{event.task.agent.role}] task complete")

        @crewai_event_bus.on(CrewKickoffCompletedEvent)
        def on_crew_completed(source, event):
            print(f"\n{'='*55}")
            print(f"🏁 Crew completed")
            print(f"{'='*55}\n")

# ── instantiate once at module level ─────────────────────
listener = SuiAdvisorListener()




# ── Crew Builder (Low and High Fidelity)─────────────────────────────────────────
def build_crew(coin: str, amount_usd: float, fidelity: str) -> Crew:
    os.makedirs("./memory", exist_ok=True)

    if fidelity == "LOW":
        return build_low_fidelity_crew(coin=coin)
    else:
        return build_high_fidelity_crew(coin=coin)


def build_low_fidelity_crew(coin: str) -> Crew:
    """
    Free APIs only — no Serper, no DUNE, no paid keys.
    4 agents: technical (Binance OHLCV) + market scraper (free URLs) +
              risk synthesis + portfolio manager.
    crypto_market_analyzer_low replaces both news and macro from HIGH mode.
    """
    technical_analysis_expert = agents.technical_analysis_expert_low(fidelity="LOW")
    crypto_market_analyzer    = agents.crypto_market_analyzer_low(fidelity="LOW")
    risk_assessment_expert    = agents.risk_assessment_expert_low(fidelity="LOW")
    crypto_portfolio_manager  = agents.crypto_portfolio_manager_low(fidelity="LOW")

    task1 = tasks.technical_analysis_task(agent=technical_analysis_expert, coin=coin)
    task2 = tasks.market_scrape_task(agent=crypto_market_analyzer, coin=coin)

    task5 = tasks.risk_assessment_task(
        agent=risk_assessment_expert,
        coin=coin,
        context=[task1, task2],
    )

    task6 = tasks.final_review_task_low(
        agent=crypto_portfolio_manager,
        coin=coin,
        context=[task5],
    )

    return Crew(
        agents=[
            technical_analysis_expert,
            crypto_market_analyzer,
            risk_assessment_expert,
            crypto_portfolio_manager,
        ],
        tasks=[task1, task2, task5, task6],
        verbose=False,
    )





def build_high_fidelity_crew(coin: str) -> Crew:
    os.makedirs("./memory", exist_ok=True)



    # Define your custom agents and tasks here (Both the 5 agenst AND the BOSS)
    onchain_data_analyst = agents.onchain_data_analyst(fidelity="HIGH")
    crypto_news_analyst = agents.crypto_news_analyst(fidelity="HIGH")
    technical_analysis_expert = agents.technical_analysis_expert(fidelity="HIGH")
    market_context_expert = agents.market_context_expert(fidelity="HIGH")
    risk_assessment_expert = agents.risk_assessment_expert(fidelity="HIGH")
    crypto_portfolio_manager = agents.crypto_portfolio_manager(fidelity="HIGH") # The BOSS (manager_agent)
    

    # tasks 1-4 run in parallel (async_execution=True)
    task1 = tasks.news_and_sentiment_task(agent=crypto_news_analyst, coin=coin)
    task2 = tasks.onchain_analysis_task(agent=onchain_data_analyst, coin=coin)
    task3 = tasks.technical_analysis_task(agent=technical_analysis_expert, coin=coin)
    task4 = tasks.macro_analysis_task(agent=market_context_expert, coin=coin)

    # task 5 waits for 1-4 via context
    task5 = tasks.risk_assessment_task(
        agent=risk_assessment_expert,
        coin=coin,
        context=[task1, task2, task3, task4],
    )

    # task 6 reviews task 5 (which already has 1-4 in context)
    task6 = tasks.final_review_task(
        agent=crypto_portfolio_manager,
        coin=coin,
        context=[task5],
    )

    return Crew(
        agents=[
            crypto_news_analyst,
            onchain_data_analyst,
            technical_analysis_expert,
            market_context_expert,
            risk_assessment_expert,
            crypto_portfolio_manager,
        ],
        tasks=[task1, task2, task3, task4, task5, task6],
        #memory=True,
        #long_term_memory=LongTermMemory(
        #    storage=LTMSQLiteStorage(db_path="./memory/sui_trading.db")
        #),
        verbose=False,
    )


# This spins up ONLY the 7th agent in isolation. The previous 6 agents don't run again. 
# CrewAI requires the Crew wrapper even for a single agent — it's just how the framework works — but the cost is minimal, 
# it's just one agent doing one task.
def run_move_script(coin: str, amount_usd: float, recommendation: str, trade_parameters: dict) -> str:
    agents_obj = SuiAgents()
    tasks_obj = SuiTradingTasks()

    writer = agents_obj.move_script_writer()
    script_task = tasks_obj.move_script_task(
        agent=writer,
        coin=coin,
        amount_usd=amount_usd,
        recommendation=recommendation,
        trade_parameters=trade_parameters,
    )

    crew = Crew(agents=[writer], tasks=[script_task], verbose=True)
    result = crew.kickoff()
    return str(result)


















# ── Scorecard Printer ─────────────────────────────────────
def print_scorecard(verdict: dict, attempt: int):
    print(f"\n{'='*55}")
    print(f"📊 SCORECARD — Attempt {attempt}")
    print(f"{'='*55}")
    print(f"Overall Confidence:  {verdict['overall_confidence']}/100")
    print(f"Recommendation:      {verdict['final_recommendation']}")
    print(f"Confidence Level:    {verdict['recommendation_confidence']}")

    print(f"\n── Agent Scores ──────────────────────────────────────")
    for agent, data in verdict["scores"].items():
        bar = "█" * data["score"] + "░" * (10 - data["score"])
        print(f"  {agent:<12} [{bar}] {data['score']}/10")
        print(f"               {data['reason']}")

    sections = [
        ("⚡ Contradictions",   "contradictions"),
        ("📭 Missing Data",     "missing_data"),
        ("🚨 Hallucinations",   "hallucinations"),
        ("⚠️  Weak Assumptions", "weak_assumptions"),
        ("🔗 Logic Gaps",       "logic_gaps"),
    ]
    for label, key in sections:
        items = verdict.get(key, [])
        if items:
            print(f"\n{label}:")
            for item in items:
                print(f"  - {item}")

    if verdict.get("trade_parameters"):
        tp = verdict["trade_parameters"]
        print(f"\n── Trade Parameters ──────────────────────────────────")
        print(f"  Entry Range:   {tp.get('entry_range', 'N/A')}")
        print(f"  Stop Loss:     {tp.get('stop_loss', 'N/A')}")
        print(f"  Take Profit 1: {tp.get('take_profit_1', 'N/A')}")
        print(f"  Take Profit 2: {tp.get('take_profit_2', 'N/A')}")
        ps = tp.get("position_size", {})
        print(f"  Position Size:")
        print(f"    Conservative: {ps.get('conservative', 'N/A')}")
        print(f"    Medium:       {ps.get('medium', 'N/A')}")
        print(f"    Aggressive:   {ps.get('aggressive', 'N/A')}")

    print(f"\n── Invalidation Conditions ───────────────────────────")
    for cond in verdict.get("invalidation_conditions", []):
        print(f"  - {cond}")

    print(f"\n── Summary ───────────────────────────────────────────")
    print(f"  {verdict.get('reason', '')}")
    print(f"{'='*55}\n")


# ── Report Saver ──────────────────────────────────────────
def save_report(verdict: dict, coin: str):
    os.makedirs("./reports", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # include fidelity and recommendation in filename
    fidelity = verdict.get("fidelity", "UNK")
    rec  = verdict.get("final_recommendation", "UNK")
    path = f"./reports/{coin}_{fidelity}_{rec}_{timestamp}.json"
    with open(path, "w") as f:
        json.dump(verdict, f, indent=2)
    print(f"📁 Report saved to {path}")



# ── at module level, outside run_crew ────────────────────
def compute_confidence(scores: dict, fidelity: str = "HIGH") -> int:

    if fidelity == "LOW":
        weights = {
            "technical": 0.60,
            "market":    0.25,
            "risk":      0.15,
        }
    else:
        weights = {
            "news":      0.15,
            "onchain":   0.25,
            "technical": 0.30,
            "macro":     0.15,
            "risk":      0.15,
        }

    def get_score(v) -> int:
        return v["score"] if isinstance(v, dict) else int(v)

    if 0 in [get_score(scores.get(k, 0)) for k in weights]:
        cap = 40
    else:
        cap = 100

    total = sum(
        get_score(scores.get(k, {"score": 0})) * w * 10
        for k, w in weights.items()
    )
    return min(int(total), cap)



#------- VERY IMPORTARNT STEP - CHECK THE OUTPUT THE AGENTS GIVNE FOR ANY MISTAKES/HALLUCINATIONS AND FIX THEM BEFORE RETURNING THE VERDICT TO THE USER
# Fix the BUY/SELL predictions if the SL/TP levels are in the wrong direction. This is a common mistake for LLMs doing trading analysis, they often mix up 
# the direction of SL/TP relative to entry. This function enforces the correct
def validate_trade_parameters(verdict: dict) -> dict:
    rec    = verdict.get("final_recommendation", "")
    params = verdict.get("trade_parameters", {})

    # ── HOLD / INSUFFICIENT DATA — clear parameters and exit ──
    if rec in ("HOLD", "INSUFFICIENT DATA"):
        verdict["trade_parameters"] = {
            "entry_range":   "N/A",
            "stop_loss":     "N/A",
            "take_profit_1": "N/A",
            "take_profit_2": "N/A",
            "position_size": {
                "conservative": "N/A",
                "medium":       "N/A",
                "aggressive":   "N/A",
            }
        }
        print(f"ℹ️  {rec} — trade parameters cleared")
        return verdict  # ← exit early, nothing else to validate

    # ── BUY / SELL only below this line ───────────────────────
    if rec not in ("BUY", "SELL"):
        return verdict

    # parse entry midpoint
    entry_raw = params.get("entry_range", "")
    prices    = re.findall(r'[\d.]+', entry_raw)
    if len(prices) < 2:
        return verdict

    entry = (float(prices[0]) + float(prices[1])) / 2

    def parse(s):
        m = re.search(r'[\d.]+', str(s))
        return float(m.group()) if m else None

    sl  = parse(params.get("stop_loss"))
    tp1 = parse(params.get("take_profit_1"))
    tp2 = parse(params.get("take_profit_2"))

    if not all([sl, tp1, tp2]):
        return verdict

    issues = []

    # ── Step 1: fix wrong direction ───────────────────────────
    if rec == "SELL":
        if sl < entry:
            correct_sl = round(entry * 1.025, 4)
            issues.append(f"SL ${sl} below entry on SELL → corrected to ${correct_sl}")
            params["stop_loss"] = f"${correct_sl}"
            sl = correct_sl
        if tp1 > entry:
            correct_tp1 = round(entry * 0.975, 4)
            issues.append(f"TP1 ${tp1} above entry on SELL → corrected to ${correct_tp1}")
            params["take_profit_1"] = f"${correct_tp1}"
            tp1 = correct_tp1
        if tp2 > entry:
            correct_tp2 = round(entry * 0.955, 4)
            issues.append(f"TP2 ${tp2} above entry on SELL → corrected to ${correct_tp2}")
            params["take_profit_2"] = f"${correct_tp2}"
            tp2 = correct_tp2

    elif rec == "BUY":
        if sl > entry:
            correct_sl = round(entry * 0.975, 4)
            issues.append(f"SL ${sl} above entry on BUY → corrected to ${correct_sl}")
            params["stop_loss"] = f"${correct_sl}"
            sl = correct_sl
        if tp1 < entry:
            correct_tp1 = round(entry * 1.025, 4)
            issues.append(f"TP1 ${tp1} below entry on BUY → corrected to ${correct_tp1}")
            params["take_profit_1"] = f"${correct_tp1}"
            tp1 = correct_tp1
        if tp2 < entry:
            correct_tp2 = round(entry * 1.045, 4)
            issues.append(f"TP2 ${tp2} below entry on BUY → corrected to ${correct_tp2}")
            params["take_profit_2"] = f"${correct_tp2}"
            tp2 = correct_tp2

    if issues:
        print(f"\n⚠️  DIRECTION CORRECTIONS:")
        for issue in issues:
            print(f"   → {issue}")

    # ── Step 2: fix values outside SUI boundaries ─────────────
    MAX_PCT = 0.05
    MIN_PCT = 0.005
    corrections = []

    current_sl  = parse(params.get("stop_loss"))
    current_tp1 = parse(params.get("take_profit_1"))
    current_tp2 = parse(params.get("take_profit_2"))

    if current_sl and abs(current_sl - entry) / entry > MAX_PCT:
        new_sl = round(entry * (0.975 if rec == "BUY" else 1.025), 4)
        corrections.append(f"SL ${current_sl} was {abs(current_sl-entry)/entry*100:.1f}% away → corrected to ${new_sl}")
        params["stop_loss"] = f"${new_sl}"

    if current_tp1 and abs(current_tp1 - entry) / entry > MAX_PCT:
        new_tp1 = round(entry * (1.025 if rec == "BUY" else 0.975), 4)
        corrections.append(f"TP1 ${current_tp1} was {abs(current_tp1-entry)/entry*100:.1f}% away → corrected to ${new_tp1}")
        params["take_profit_1"] = f"${new_tp1}"

    if current_tp2 and abs(current_tp2 - entry) / entry > MAX_PCT:
        new_tp2 = round(entry * (1.045 if rec == "BUY" else 0.955), 4)
        corrections.append(f"TP2 ${current_tp2} was {abs(current_tp2-entry)/entry*100:.1f}% away → corrected to ${new_tp2}")
        params["take_profit_2"] = f"${new_tp2}"

    if current_sl and abs(current_sl - entry) / entry < MIN_PCT:
        corrections.append(f"⚠️  SL ${current_sl} is only {abs(current_sl-entry)/entry*100:.2f}% from entry — too tight")

    if corrections:
        print(f"\n⚠️  BOUNDARY CORRECTIONS:")
        for c in corrections:
            print(f"   → {c}")
        verdict["parameter_corrections"] = (verdict.get("parameter_corrections", []) + corrections)

    verdict["trade_parameters"] = params
    return verdict


# ── Main Loop ─────────────────────────────────────────────
def run_crew(amount_usd: float, fidelity: str) -> dict:
    result = None
    verdict = None  # ← initialize here so it's always defined

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"\n{'='*55}")
        print(f"🔄 Attempt {attempt} of {MAX_RETRIES} — ${amount_usd} of {coin} [{fidelity} fidelity]")
        print(f"{'='*55}\n")

        crew = build_crew(coin, amount_usd, fidelity)  # ← coin is fixed, amount_usd is used ONLY by the 7th Agent, fidelity is used by all
        result = crew.kickoff()

        try:
            raw = str(result).strip()

            # extract JSON block
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if not match:
                raise json.JSONDecodeError("No JSON found in output", raw, 0)

            clean = match.group()

            # strip markdown fences if present
            clean = re.sub(r'^```json\s*', '', clean)
            clean = re.sub(r'```$', '', clean)
            clean = clean.strip()

            # fix trailing commas before } or ] (common LLM mistake)
            clean = re.sub(r',\s*([}\]])', r'\1', clean)

            verdict = json.loads(clean)


            # ── validate and correct trade parameters ────────────────
            verdict = validate_trade_parameters(verdict)


            # ── always override confidence with computed value ──
            # never trust what the agent self-reports
            computed_confidence = compute_confidence(verdict["scores"], fidelity=fidelity)
            verdict["overall_confidence"] = computed_confidence
            verdict["amount_usd"] = amount_usd  # attach for 7th agent

            # before
            #approved = verdict["approved"]

            # after  (derive "approved" from computed confidence, never trust the agent)
            verdict["approved"] = computed_confidence >= CONFIDENCE_THRESHOLD
            approved = verdict["approved"]



            confidence = computed_confidence  # use computed, not agent's

            print_scorecard(verdict, attempt)

            if approved and confidence >= CONFIDENCE_THRESHOLD:
                print(f"✅ APPROVED — Confidence: {confidence}/100")
                verdict["fidelity"] = fidelity          # ← add this
                verdict["amount_usd"] = amount_usd      # ← already there
                verdict["timestamp"] = datetime.now().isoformat()  # ← add this
                save_report(verdict, coin) # ← always save
                return verdict
            else:
                print(f"⚠️  REJECTED — Confidence: {confidence}/100 "
                      f"(threshold: {CONFIDENCE_THRESHOLD})")
                print(f"   Failed agents: {verdict.get('failed_agents', [])}")
                print(f"   Reason: {verdict.get('reason', 'Unknown')}")
                if attempt < MAX_RETRIES:
                    print(f"\n🔁 Retrying...\n")

        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️  Could not parse verdict on attempt {attempt}: {e}")
            if attempt < MAX_RETRIES:
                print("🔁 Retrying...\n")

    # ── all retries exhausted ─────────────────────────────
    print("\n❌ Max retries reached")

    if verdict is not None:
        # we parsed something but it never hit the threshold — return it anyway
        verdict["amount_usd"] = amount_usd
        return verdict

    # never parsed anything at all
    return {
        "error": "Max retries reached — could not parse verdict",
        "raw": str(result),
        "amount_usd": amount_usd,
        "final_recommendation": "INSUFFICIENT DATA",
        "overall_confidence": 0,
        "approved": False,
    }












# ── Entry Point (Starting prompt message + Parameters) ───────────────────────────────────────────
# if __name__ == "__main__":
#     print("\n## Welcome to the SUI Trading Advisor")
#     print("-" * 40)
#     coin = input("What crypto coin are you interested in? ").strip()
#     run_crew(coin)

if __name__ == "__main__":
    print("\n## Welcome to the SUI Trading Advisor")
    print("-" * 40)
    amount_usd = float(input("Amount in USD: $").strip())
    fidelity = input("Fidelity (LOW or HIGH): ").strip().upper()
    run_crew(amount_usd=amount_usd, fidelity=fidelity)