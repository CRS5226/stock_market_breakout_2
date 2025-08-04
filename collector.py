import os
import time
import pandas as pd
from dotenv import load_dotenv
from breeze_connect import BreezeConnect

load_dotenv()

API_KEY = os.getenv("BREEZE_API_KEY")
API_SECRET = os.getenv("BREEZE_API_SECRET")
SESSION_TOKEN = os.getenv("BREEZE_SESSION_TOKEN")


def start_collector(shared_data, stock_code="HDFBAN"):
    df = pd.DataFrame()

    breeze = BreezeConnect(api_key=API_KEY)
    breeze.generate_session(api_secret=API_SECRET, session_token=SESSION_TOKEN)

    print(f"🟢 Collector started for {stock_code}")

    def on_ticks(ticks):
        nonlocal df
        tick = ticks[0] if isinstance(ticks, list) else ticks

        try:
            timestamp = pd.to_datetime(tick.get("ltt"))

            new_row = {
                "Timestamp": timestamp,
                "Open": tick.get("open"),
                "High": tick.get("high"),
                "Low": tick.get("low"),
                "Close": tick.get("last"),
                "PrevClose": tick.get("close"),  # Previous close
                "Change": tick.get("change"),
                "Volume": tick.get("ltq"),  # Last traded quantity
                "TotalVolume": tick.get("ttq"),  # Total traded quantity
                "BuyQty": tick.get("bQty"),
                "SellQty": tick.get("sQty"),
                "BuyPrice": tick.get("bPrice"),
                "SellPrice": tick.get("sPrice"),
                "TotalBuyQty": tick.get("totalBuyQt"),
                "TotalSellQty": tick.get("totalSellQ"),
                "AvgPrice": tick.get("avgPrice"),
                "UpperCircuit": tick.get("upperCktLm"),
                "LowerCircuit": tick.get("lowerCktLm"),
                "Exchange": tick.get("exchange"),
                "StockName": tick.get("stock_name"),
                "Trend": tick.get("trend") or "",
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df = df.tail(500)  # Maintain rolling window

            shared_data[stock_code] = df.to_json()

        except Exception as e:
            print(f"[{stock_code}] Tick processing error: {e}")

    breeze.on_ticks = on_ticks
    breeze.ws_connect()

    try:
        breeze.subscribe_feeds(
            exchange_code="NSE",
            stock_code=stock_code,
            product_type="cash",
            get_market_depth=False,
            get_exchange_quotes=True,
        )
    except Exception as e:
        print(f"[{stock_code}] Subscription error: {e}")

    while True:
        time.sleep(1)
