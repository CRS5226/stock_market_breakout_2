# server.py

import time
import json
import io
from multiprocessing import Manager, Process
import pandas as pd

from indicator import is_breakout, add_indicators
from collector import start_collector
from telegram_alert import send_trade_alert, send_pipeline_status, send_error_alert

BREAKOUT_STATE = {}
LAST_CONFIG = {}
CONFIG_PATH = "config.json"


def load_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Config Error] Failed to read config.json: {e}")
        return {"stocks": []}


def fetch_latest_config_for_stock(stock_code):
    config = load_config()
    for stock in config.get("stocks", []):
        if stock["stock_code"] == stock_code:
            return stock
    return None


def print_config_changes(stock_code, new_config):
    last_config = LAST_CONFIG.get(stock_code, {})
    messages = []

    for key in new_config:
        new_val = new_config.get(key)
        old_val = last_config.get(key)

        if isinstance(new_val, dict):
            for sub_key in new_val:
                old_sub = old_val.get(sub_key) if old_val else None
                new_sub = new_val[sub_key]
                if old_sub != new_sub:
                    messages.append(f"{key}.{sub_key}: {old_sub} → {new_sub}")
        else:
            if old_val != new_val:
                messages.append(f"{key}: {old_val} → {new_val}")

    if messages:
        print(f"[🔁 CONFIG CHANGE] {stock_code} → " + ", ".join(messages))


def monitor_stock(shared_data, initial_config):
    stock_code = initial_config["stock_code"]

    LAST_CONFIG[stock_code] = initial_config.copy()
    BREAKOUT_STATE[stock_code] = {"above_resistance": False, "below_support": False}

    while True:
        try:
            updated_config = fetch_latest_config_for_stock(stock_code)
            if not updated_config:
                print(f"[⚠️ WARNING] {stock_code} config not found in latest config.")
                time.sleep(2)
                continue

            support = updated_config.get("support", 0)
            resistance = updated_config.get("resistance", 0)

            if (
                LAST_CONFIG[stock_code].get("support") != support
                or LAST_CONFIG[stock_code].get("resistance") != resistance
            ):
                print_config_changes(stock_code, updated_config)
                LAST_CONFIG[stock_code] = updated_config.copy()
                BREAKOUT_STATE[stock_code] = {
                    "above_resistance": False,
                    "below_support": False,
                }

            if stock_code in shared_data:
                df = pd.read_json(io.StringIO(shared_data[stock_code]))

                if len(df) < 10:
                    time.sleep(1)
                    continue

                df = add_indicators(df, updated_config)
                signal, price, levels, reason = is_breakout(
                    df, resistance, support, updated_config
                )

                filename = f"latest_data_{stock_code.upper()}.csv"
                df.to_csv(filename, index=False)
                print(
                    f"[{df['Timestamp'].iloc[-1]}] 💾 {stock_code}: Saved {len(df)} rows to {filename}"
                )

                state = BREAKOUT_STATE[stock_code]

                if signal == "breakout" and not state["above_resistance"]:
                    msg = f"📈 Breakout Above Resistance (₹{resistance})\n🧠 Reason: {reason}"
                    print(f"[📢 ALERT] {stock_code} {msg} at ₹{price}")
                    send_trade_alert(stock_code, msg, price, df["Timestamp"].iloc[-1])
                    state["above_resistance"] = True
                    state["below_support"] = False

                elif signal == "breakdown" and not state["below_support"]:
                    msg = (
                        f"📉 Breakdown Below Support (₹{support})\n🧠 Reason: {reason}"
                    )
                    print(f"[📢 ALERT] {stock_code} {msg} at ₹{price}")
                    send_trade_alert(stock_code, msg, price, df["Timestamp"].iloc[-1])
                    state["below_support"] = True
                    state["above_resistance"] = False

            time.sleep(2)

        except Exception as e:
            error_msg = f"[{stock_code}] Monitor Error: {type(e).__name__}: {e}"
            print(f"[TELEGRAM DEBUG] Sending Error: {error_msg}")
            send_error_alert(error_msg)
            time.sleep(5)


def run():
    manager = Manager()
    shared_data = manager.dict()
    processes = {}

    print("🚀 Real-Time Stock Monitor started. Watching for changes...")

    while True:
        try:
            config = load_config()
            stock_list = config.get("stocks", [])
            existing_codes = set(processes.keys())

            for stock in stock_list:
                code = stock["stock_code"]
                if code not in existing_codes:
                    print(f"[🆕 NEW STOCK] {code} added — starting pipeline...")

                    # Start collector
                    collector_proc = Process(
                        target=start_collector, args=(shared_data, code)
                    )
                    collector_proc.start()

                    # Start monitor
                    monitor_proc = Process(
                        target=monitor_stock, args=(shared_data, stock)
                    )
                    monitor_proc.start()

                    # Track them
                    processes[code] = {
                        "collector": collector_proc,
                        "monitor": monitor_proc,
                    }

                    LAST_CONFIG[code] = stock.copy()
                    BREAKOUT_STATE[code] = {
                        "above_resistance": False,
                        "below_support": False,
                    }

                    send_pipeline_status("✅ Started Monitoring", code)

            time.sleep(5)

        except KeyboardInterrupt:
            print("⛔️ Stopped by user.")
            break
        except Exception as e:
            error_msg = f"[Server Error] {type(e).__name__}: {e}"
            print(f"[TELEGRAM DEBUG] Sending Error: {error_msg}")
            send_error_alert(error_msg)
            time.sleep(5)


if __name__ == "__main__":
    run()
