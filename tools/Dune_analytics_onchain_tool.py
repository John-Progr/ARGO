from crewai.tools import BaseTool
import requests


class SUIOnChainTool(BaseTool):
    name: str = "SUI On-Chain Data Tool"

    description: str = """
    Fetches live on-chain and market metrics for the SUI ecosystem.

    Sources (no API keys required):
    - Sui mainnet RPC: total transactions, epoch, active validators, total stake
    - DefiLlama:       Sui chain TVL (USD)
    - CoinGecko:       SUI token price, 24h volume, market cap, 24h price change

    Input: the coin symbol to analyse (e.g. "SUI"). Ignored internally —
    always returns Sui ecosystem data.

    Returns a structured text summary suitable for risk assessment.
    """

    def _run(self, coin: str = "SUI") -> str:  # noqa: ARG002
        results = {}
        errors = []

        # ── 1. Sui mainnet RPC ────────────────────────────────────────────────
        try:
            rpc = "https://fullnode.mainnet.sui.io:443"
            headers = {"Content-Type": "application/json"}

            r_tx = requests.post(
                rpc,
                json={"jsonrpc": "2.0", "id": 1,
                      "method": "sui_getTotalTransactionBlocks", "params": []},
                headers=headers, timeout=10,
            )
            results["total_transactions"] = r_tx.json().get("result", "N/A")

            r_sys = requests.post(
                rpc,
                json={"jsonrpc": "2.0", "id": 2,
                      "method": "suix_getLatestSuiSystemState", "params": []},
                headers=headers, timeout=10,
            )
            sys_state = r_sys.json().get("result", {})
            results["epoch"]             = sys_state.get("epoch", "N/A")
            results["active_validators"] = len(sys_state.get("activeValidators", []))
            raw_stake = sys_state.get("totalStake", 0)
            results["total_stake_sui"]   = round(int(raw_stake) / 1e9, 0) if raw_stake else "N/A"
        except Exception as e:
            errors.append(f"Sui RPC error: {e}")

        # ── 2. DefiLlama — Sui chain TVL ──────────────────────────────────────
        try:
            r_chains = requests.get(
                "https://api.llama.fi/v2/chains", timeout=10
            )
            chains = r_chains.json()
            sui_chain = next(
                (c for c in chains if c.get("name", "").lower() == "sui"), None
            )
            results["tvl_usd"] = (
                f"${sui_chain['tvl'] / 1e6:.1f}M" if sui_chain else "N/A"
            )
        except Exception as e:
            errors.append(f"DefiLlama error: {e}")

        # ── 3. CoinGecko — SUI token market data ──────────────────────────────
        try:
            r_cg = requests.get(
                "https://api.coingecko.com/api/v3/coins/sui",
                params={
                    "localization": "false",
                    "tickers": "false",
                    "community_data": "false",
                    "developer_data": "false",
                },
                timeout=10,
            )
            md = r_cg.json().get("market_data", {})
            results["price_usd"]         = md.get("current_price", {}).get("usd", "N/A")
            results["volume_24h_usd"]    = f"${md.get('total_volume', {}).get('usd', 0) / 1e6:.1f}M"
            results["market_cap_usd"]    = f"${md.get('market_cap', {}).get('usd', 0) / 1e9:.2f}B"
            results["price_change_24h"]  = f"{md.get('price_change_percentage_24h', 0):.2f}%"
            results["price_change_7d"]   = f"{md.get('price_change_percentage_7d', 0):.2f}%"
        except Exception as e:
            errors.append(f"CoinGecko error: {e}")

        # ── Format output ──────────────────────────────────────────────────────
        if not results:
            return "Error: all on-chain data sources failed. " + " | ".join(errors)

        lines = ["SUI On-Chain & Market Metrics", "=" * 40]

        field_labels = {
            "total_transactions":  "Total Transactions (mainnet)",
            "epoch":               "Current Epoch",
            "active_validators":   "Active Validators",
            "total_stake_sui":     "Total Staked (SUI)",
            "tvl_usd":             "DeFi TVL (USD)",
            "price_usd":           "Price (USD)",
            "volume_24h_usd":      "24h Volume",
            "market_cap_usd":      "Market Cap",
            "price_change_24h":    "Price Change 24h",
            "price_change_7d":     "Price Change 7d",
        }

        for key, label in field_labels.items():
            if key in results:
                lines.append(f"  {label:<30} {results[key]}")

        if errors:
            lines.append("")
            lines.append("Partial errors: " + " | ".join(errors))

        return "\n".join(lines)
