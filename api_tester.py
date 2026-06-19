import requests
import json

# Each entry in prices is [unix_timestamp_ms, price_usd] — which is exactly what the evaluator uses to find the price closest to your recommendation timestamp.


response = requests.get(
    "https://api.coingecko.com/api/v3/coins/sui/market_chart",
    params={
        "vs_currency": "usd",
        "days": 14,
        "interval": "daily",
    },
    timeout=10,
)

data = response.json()
print(json.dumps(data, indent=2))