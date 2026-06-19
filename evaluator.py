# evaluator.py
import json
import os
import re
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path

EVALUATION_WINDOW_DAYS = 1  # check price 24h after recommendation


def get_sui_price_at(target_datetime: datetime) -> float | None:
    """Fetch SUI price closest to a target datetime using CoinGecko free API"""
    try:
        # CoinGecko market_chart gives daily prices for free
        response = requests.get(
            "https://api.coingecko.com/api/v3/coins/sui/market_chart",
            params={
                "vs_currency": "usd",
                "days": 14,
                "interval": "daily",
            },
            timeout=10,
        )
        response.raise_for_status()
        prices = response.json()["prices"]  # [[unix_ms, price], ...]

        target_ms = int(target_datetime.timestamp()) * 1000
        closest = min(prices, key=lambda p: abs(p[0] - target_ms))
        return closest[1]

    except Exception as e:
        print(f"  ⚠️  CoinGecko error: {e}")
        return None


def parse_price(s: str) -> float | None:
    """Extract first number from a price string like '$0.73'"""
    m = re.search(r'[\d.]+', str(s))
    return float(m.group()) if m else None


def evaluate_report(report_path: str) -> dict | None:
    with open(report_path) as f:
        report = json.load(f)

    timestamp  = report.get("timestamp")
    rec        = report.get("final_recommendation")
    confidence = report.get("overall_confidence", 0)
    fidelity   = report.get("fidelity", "UNKNOWN")
    params     = report.get("trade_parameters", {})

    # skip HOLD and INSUFFICIENT DATA — no direction to evaluate
    if not timestamp or rec not in ("BUY", "SELL"):
        print(f"  ⏭️  Skipping {os.path.basename(report_path)} — {rec}")
        return None

    # check if enough time has passed
    rec_time  = datetime.fromisoformat(timestamp)
    eval_time = rec_time + timedelta(days=EVALUATION_WINDOW_DAYS)
    if eval_time > datetime.now():
        print(f"  ⏳ Too early to evaluate {os.path.basename(report_path)} — check after {eval_time.strftime('%Y-%m-%d %H:%M')}")
        return None

    # parse trade parameters
    entry_raw = params.get("entry_range", "")
    prices    = re.findall(r'[\d.]+', entry_raw)
    entry     = (float(prices[0]) + float(prices[1])) / 2 if len(prices) >= 2 else None
    sl        = parse_price(params.get("stop_loss"))
    tp1       = parse_price(params.get("take_profit_1"))
    tp2       = parse_price(params.get("take_profit_2"))

    if not all([entry, sl, tp1, tp2]):
        print(f"  ⚠️  Missing trade parameters in {os.path.basename(report_path)}")
        return None

    # fetch price at evaluation time
    print(f"  📡 Fetching price for {os.path.basename(report_path)}...")
    price_at_eval = get_sui_price_at(eval_time)
    time.sleep(1.5)  # respect CoinGecko rate limit

    if price_at_eval is None:
        return None

    # score the outcome
    if rec == "BUY":
        correct = price_at_eval > entry
        hit_tp1 = price_at_eval >= tp1
        hit_tp2 = price_at_eval >= tp2
        hit_sl  = price_at_eval <= sl
    else:  # SELL
        correct = price_at_eval < entry
        hit_tp1 = price_at_eval <= tp1
        hit_tp2 = price_at_eval <= tp2
        hit_sl  = price_at_eval >= sl

    result = {
        "file":           os.path.basename(report_path),
        "timestamp":      timestamp,
        "fidelity":       fidelity,
        "recommendation": rec,
        "confidence":     confidence,
        "entry":          entry,
        "sl":             sl,
        "tp1":            tp1,
        "tp2":            tp2,
        "price_at_eval":  price_at_eval,
        "correct":        correct,
        "hit_tp1":        hit_tp1,
        "hit_tp2":        hit_tp2,
        "hit_sl":         hit_sl,
        "eval_window_days": EVALUATION_WINDOW_DAYS,
    }

    status = "✅" if correct else "❌"
    print(f"  {status} {rec} @ ${entry:.4f} → price ${price_at_eval:.4f} after {EVALUATION_WINDOW_DAYS}d")
    return result


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
        tp1_hits = sum(1 for r in subset if r["hit_tp1"])
        tp2_hits = sum(1 for r in subset if r["hit_tp2"])
        sl_hits  = sum(1 for r in subset if r["hit_sl"])

        print(f"\n{'─'*40}")
        print(f"  {fidelity} FIDELITY — {n} evaluations")
        print(f"{'─'*40}")
        print(f"  Directional Accuracy: {correct/n*100:.1f}% ({correct}/{n})")
        print(f"  TP1 Hit Rate:         {tp1_hits/n*100:.1f}% ({tp1_hits}/{n})")
        print(f"  TP2 Hit Rate:         {tp2_hits/n*100:.1f}% ({tp2_hits}/{n})")
        print(f"  Stop Loss Rate:       {sl_hits/n*100:.1f}% ({sl_hits}/{n})")

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

    # save full results
    out_path = reports_dir / "evaluation.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Full results saved to {out_path}")

    print_summary(results)


if __name__ == "__main__":
    run_evaluation()