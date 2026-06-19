import requests
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands



# Newer version of CrewAI do not support tools through langchain.tools, so we import BaseTool directly from crewai.tools and 
# define our tool as a class that inherits from BaseTool. The _run method is where the logic of fetching data and computing indicators goes.
from crewai.tools import BaseTool


class SuiPriceDataTool(BaseTool):
    name: str = "SUI Price Data Tool"
    description: str = """
    Fetches OHLCV price data for SUI and computes RSI, MACD, and Bollinger Bands.
    Input: interval string (1d, 4h, 1h). Default is 1d.
    """

    def _run(self, interval: str = "1d") -> str:
        try:
            interval = interval.strip().strip("'").strip('"')
            limit = "90"

            url = "https://api.binance.com/api/v3/klines"
            params = {
                "symbol": "SUIUSDT",
                "interval": interval,
                "limit": limit
            }

            response = requests.get(url, params=params)
            data = response.json()

            if not data:
                return "Error: No data returned from Binance API"

            df = pd.DataFrame(data, columns=[
                "timestamp", "open", "high", "low", "close", "volume",
                "close_time", "quote_volume", "trades",
                "taker_buy_base", "taker_buy_quote", "ignore"
            ])

            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df = df[["timestamp", "open", "high", "low", "close", "volume"]]
            df = df.astype({"open": float, "high": float, "low": float, "close": float, "volume": float})

            if len(df) < 20:
                return "Error: Not enough data"

            df["rsi"] = RSIIndicator(df["close"], window=14).rsi()
            macd = MACD(df["close"])
            df["macd"] = macd.macd()
            df["macd_signal"] = macd.macd_signal()

            bb = BollingerBands(df["close"], window=20)
            df["bb_upper"] = bb.bollinger_hband()
            df["bb_lower"] = bb.bollinger_lband()

            latest = df.iloc[-1]

            return f"""
SUI Price Analysis (interval={interval})

Close: {latest['close']:.4f}
RSI: {latest['rsi']:.2f}
MACD: {latest['macd']:.4f}
Signal: {latest['macd_signal']:.4f}
"""
        except Exception as e:
            return f"Error: {str(e)}"