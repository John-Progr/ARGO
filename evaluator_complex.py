# evaluator.py
import json
import os
import re
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path

EVALUATION_WINDOW_DAYS = 1


def get_hourly_prices(timestamp: str, days: int = 3) -> list:
    """Get hourly prices for N days after timestamp"""
    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/coins/sui/market_chart",
            params={
                "vs_currency": "usd",
                "days": days,
                "interval": "hourly",
            },
            timeout=10,
        )
        data = response.json()
        prices = data["prices"]  # [[unix_ms, price], ...]

        rec_time_ms = int(datetime.fromisoformat(timestamp).timestamp()) * 1000
        return [p for p in prices if p[0] >= rec_time_ms]

    except Exception as e:
        print(f"CoinGecko error: {e}")
        return []


def parse_price(s: str) -> float | None:
    """Extract first number from a price string like '$0.73'"""
    m = re.search(r'[\d.]+', str(s))
    return float(m.group()) if m else None


# ── must be defined BEFORE evaluate_report ───────────────
def evaluate_outcome(rec: str, entry: float, sl: float, tp1: float,
                     tp2: float, hourly_prices: list) -> dict:
    """
    Simulate the trade hour by hour.
    Check which level is hit first — TP1, TP2, or SL.
    """
    tp1_hit_time  = None
    tp2_hit_time  = None
    sl_hit_time   = None
    first_outcome = None

    for unix_ms, price in hourly_prices:
        dt = datetime.fromtimestamp(unix_ms / 1000)

        if rec == "BUY":
            if sl_hit_time is None and price <= sl:
                sl_hit_time = dt
                if first_outcome is None:
                    first_outcome = "SL"
            if tp1_hit_time is None and price >= tp1:
                tp1_hit_time = dt
                if first_outcome is None:
                    first_outcome = "TP1"
            if tp2_hit_time is None and price >= tp2:
                tp2_hit_time = dt
                if first_outcome is None:
                    first_outcome = "TP2"

        else:  # SELL
            if sl_hit_time is None and price >= sl:
                sl_hit_time = dt
                if first_outcome is None:
                    first_outcome = "SL"
            if tp1_hit_time is None and price <= tp1:
                tp1_hit_time = dt
                if first_outcome is None:
                    first_outcome = "TP1"
            if tp2_hit_time is None and price <= tp2:
                tp2_hit_time = dt
                if first_outcome is None:
                    first_outcome = "TP2"

    # nothing hit — check final price direction
    if first_outcome is None:
        final_price = hourly_prices[-1][1] if hourly_prices else entry
        if rec == "BUY":
            first_outcome = "PROFIT" if final_price > entry else "LOSS"
        else:
            first_outcome = "PROFIT" if final_price < entry else "LOSS"

    return {
        "first_outcome": first_outcome,
        "sl_hit":        sl_hit_time is not None,
        "tp1_hit":       tp1_hit_time is not None,
        "tp2_hit":       tp2_hit_time is not None,
        "sl_hit_time":   sl_hit_time.isoformat() if sl_hit_time else None,
        "tp1_hit_time":  tp1_hit_time.isoformat() if tp1_hit_time else None,
        "tp2_hit_time":  tp2_hit_time.isoformat() if tp2_hit_time else None,
        "correct":       first_outcome in ("TP1", "TP2", "PROFIT"),
    }


def evaluate_report(report_path: str) -> dict | None:
    with open(report_path) as f:
        report = json.load(f)

    timestamp  = report.get("timestamp")
    rec        = report.get("final_recommendation")
    confidence = report.get("overall_confidence", 0)
    fidelity   = report.get("fidelity", "UNKNOWN")
    params     = report.get("trade_parameters", {})

    if not timestamp or rec not in ("BUY", "SELL"):
        print(f"  ⏭️  Skipping {os.path.basename(report_path)} — {rec}")
        return None

    rec_time  = datetime.fromisoformat(timestamp)
    eval_time = rec_time + timedelta(days=EVALUATION_WINDOW_DAYS)
    if eval_time > datetime.now():
        print(f"  ⏳ Too early — check after {eval_time.strftime('%Y-%m-%d %H:%M')}")
        return None

    entry_raw = params.get("entry_range", "")
    prices    = re.findall(r'[\d.]+', entry_raw)
    entry     = (float(prices[0]) + float(prices[1])) / 2 if len(prices) >= 2 else None
    sl        = parse_price(params.get("stop_loss"))
    tp1       = parse_price(params.get("take_profit_1"))
    tp2       = parse_price(params.get("take_profit_2"))

    if not all([entry, sl, tp1, tp2]):
        print(f"  ⚠️  Missing trade parameters in {os.path.basename(report_path)}")
        return None

    print(f"  📡 Fetching hourly prices for {os.path.basename(report_path)}...")
    hourly_prices = get_hourly_prices(timestamp, days=3)
    time.sleep(1.5)

    if not hourly_prices:
        return None

    outcome = evaluate_outcome(rec, entry, sl, tp1, tp2, hourly_prices)

    status = "✅" if outcome["correct"] else "❌"
    print(f"  {status} {rec} entry ${entry:.4f} → first outcome: {outcome['first_outcome']}")

    return {
        "file":           os.path.basename(report_path),
        "timestamp":      timestamp,
        "fidelity":       fidelity,
        "recommendation": rec,
        "confidence":     confidence,
        "entry":          entry,
        "sl":             sl,
        "tp1":            tp1,
        "tp2":            tp2,
        "first_outcome":  outcome["first_outcome"],
        "correct":        outcome["correct"],
        "sl_hit":         outcome["sl_hit"],
        "tp1_hit":        outcome["tp1_hit"],
        "tp2_hit":        outcome["tp2_hit"],
        "sl_hit_time":    outcome["sl_hit_time"],
        "tp1_hit_time":   outcome["tp1_hit_time"],
        "tp2_hit_time":   outcome["tp2_hit_time"],
    }


def print_summary(results: list):
    print(f"\n{'='*50}")
    print(f"📊 EVALUATION SUMMARY")
    print(f"{'='*50}")

    for fidelity in ["LOW", "HIGH"]:
        subset = [r for r in results if r["fidelity"] == fidelity]
        if not subset:
            continue

        n        = len(subset)
        correct  = sum(1 for r in subset if r["correct"])
        tp1_hits = sum(1 for r in subset if r["tp1_hit"])   # ← fixed key
        tp2_hits = sum(1 for r in subset if r["tp2_hit"])   # ← fixed key
        sl_hits  = sum(1 for r in subset if r["sl_hit"])    # ← fixed key

        print(f"\n{'─'*40}")
        print(f"  {fidelity} FIDELITY — {n} evaluations")
        print(f"{'─'*40}")
        print(f"  Directional Accuracy: {correct/n*100:.1f}% ({correct}/{n})")
        print(f"  TP1 Hit Rate:         {tp1_hits/n*100:.1f}% ({tp1_hits}/{n})")
        print(f"  TP2 Hit Rate:         {tp2_hits/n*100:.1f}% ({tp2_hits}/{n})")
        print(f"  Stop Loss Rate:       {sl_hits/n*100:.1f}% ({sl_hits}/{n})")

        # outcome breakdown
        outcomes = {}
        for r in subset:
            o = r["first_outcome"]
            outcomes[o] = outcomes.get(o, 0) + 1
        print(f"  Outcome breakdown:")
        for o, count in sorted(outcomes.items()):
            print(f"    {o}: {count} ({count/n*100:.1f}%)")

        # confidence breakdown
        high_conf = [r for r in subset if r["confidence"] >= 70]
        low_conf  = [r for r in subset if r["confidence"] < 70]
        if high_conf:
            hc_acc = sum(1 for r in high_conf if r["correct"]) / len(high_conf) * 100
            print(f"  Accuracy ≥70 conf:    {hc_acc:.1f}% ({len(high_conf)} runs)")
        if low_conf:
            lc_acc = sum(1 for r in low_conf if r["correct"]) / len(low_conf) * 100
            print(f"  Accuracy <70 conf:    {lc_acc:.1f}% ({len(low_conf)} runs)")

    print(f"\n{'='*50}")
    print(f"  Total evaluated: {len(results)}")
    print(f"{'='*50}\n")


def run_evaluation():
    reports_dir = Path("./reports")
    results     = []

    print(f"\n🔍 Scanning {reports_dir} for reports...\n")

    for path in sorted(reports_dir.glob("SUI_*.json")):
        if path.name == "evaluation.json":
            continue
        result = evaluate_report(str(path))
        if result:
            results.append(result)

    if not results:
        print("⚠️  No evaluable results yet — check back after evaluation window passes")
        return

    out_path = reports_dir / "evaluation.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Full results saved to {out_path}")

    print_summary(results)


if __name__ == "__main__":
    run_evaluation()