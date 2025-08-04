# app.py

import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime
from indicator import is_breakout
from groq_forecast import forecast_stock

CONFIG_FILE = "config.json"

st.set_page_config(page_title="📈 Live Stock Monitor", layout="wide")
st.title("📊 Real-Time Multi-Stock Monitor")

DATA_CSV_PATH = "data.csv"


def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {"stocks": []}


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


if "breakout_shown" not in st.session_state:
    st.session_state.breakout_shown = {}
if "toast_shown_time" not in st.session_state:
    st.session_state.toast_shown_time = {}


def load_company_list():
    try:
        df = pd.read_csv(DATA_CSV_PATH)  # CSV separator assumed default (comma)

        # Check for required columns
        required_cols = ["ScripName", "CompanyName", "ShortName"]
        if not all(col in df.columns for col in required_cols):
            st.error(f"CSV is missing one of the required columns: {required_cols}")
            return pd.DataFrame(columns=required_cols)

        return df[required_cols].dropna().drop_duplicates()
    except Exception as e:
        st.error(f"Error loading company list: {e}")
        return pd.DataFrame(columns=["ScripName", "CompanyName", "ShortName"])


st.subheader("➕ Add Stock to Monitor")
company_df = load_company_list()

# Create dropdown display name and map it to ShortName
company_map = {
    f"{row['CompanyName']} ({row['ScripName']})": row["ShortName"]
    for _, row in company_df.iterrows()
}

new_company = st.selectbox("Select a stock to monitor", [""] + list(company_map.keys()))

if new_company:
    new_code = company_map[new_company]  # This is now the ShortName
    config = load_config()
    stock_codes = [s["stock_code"] for s in config.get("stocks", [])]

    if new_code not in stock_codes:
        default_entry = {
            "stock_code": new_code,
            "support": 1000,
            "resistance": 1100,
            "volume_threshold": 100000,
            "bollinger": {"period": 20, "std_dev": 2.0},
            "macd": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
            "adx": {"period": 14, "threshold": 25},
            "moving_averages": {"ma_fast": 9, "ma_slow": 21},
            "inside_bar": {"lookback": 1},
            "candle": {"min_body_percent": 0.7},
        }

        config["stocks"].append(default_entry)
        save_config(config)
        st.success(f"✅ Added {new_company} with default parameters.")
        st.rerun()

    else:
        st.info("Already added.")


# def load_latest_df(stock_code):
#     try:
#         df = pd.read_csv(f"latest_data_{stock_code}.csv")
#         if len(df) > 0:
#             df = df.sort_values("Timestamp")
#             return df
#         else:
#             return None
#     except:
#         return None


def load_latest_df(stock_code):
    try:
        df = pd.read_csv(f"latest_data_{stock_code}.csv")
        if len(df) == 0:
            return None

        # Normalize column names for lowercase CSVs (like TCS)
        if "datetime" in df.columns:
            df = df.rename(
                columns={
                    "datetime": "Timestamp",
                    "open": "Open",
                    "high": "High",
                    "low": "Low",
                    "close": "Close",
                    "volume": "Volume",
                }
            )

            # Add missing columns
            # if "PrevClose" not in df.columns:
            #     df["PrevClose"] = None
            # if "Change" not in df.columns:
            #     df["Change"] = None

        # Ensure 'Timestamp' exists before sorting
        if "Timestamp" not in df.columns:
            return None

        df = df.sort_values("Timestamp")
        return df

    except Exception as e:
        print(f"[!] Error loading {stock_code}: {e}")
        return None


def toast(message, type="info"):
    if type == "success":
        st.success(message)
    elif type == "error":
        st.error(message)
    elif type == "warning":
        st.warning(message)
    else:
        st.info(message)


def render_cards():
    config = load_config()
    stocks = config.get("stocks", [])

    cols = st.columns(5)

    for i, stock in enumerate(stocks):
        code = stock["stock_code"]
        with cols[i % 5].container(border=True):
            df = load_latest_df(code)
            if df is None:
                st.warning(f"⏳ Waiting for {code} data...")
                continue

            st.subheader(code)
            st.metric("Latest Price", f"₹{df['Close'].iloc[-1]:.2f}")
            st.caption(f"Updated: {df['Timestamp'].iloc[-1]}")

            # === Threshold Inputs ===
            new_support = st.number_input(
                f"{code} Support",
                value=stock.get("support", 0),
                step=1,
                key=f"{code}_support",
            )
            new_resistance = st.number_input(
                f"{code} Resistance",
                value=stock.get("resistance", 0),
                step=1,
                key=f"{code}_resistance",
            )
            new_volume = st.number_input(
                f"{code} Volume Threshold",
                value=stock.get("volume_threshold", 0),
                step=1000,
                key=f"{code}_volume",
            )

            # # === Bollinger Bands ===
            # bb = stock.get("bollinger", {})
            # bb_period = st.number_input(
            #     f"{code} Bollinger Period",
            #     value=bb.get("period", 20),
            #     step=1,
            #     key=f"{code}_bb_period",
            # )
            # bb_std = st.number_input(
            #     f"{code} Bollinger Std Dev",
            #     value=float(bb.get("std_dev", 2)),
            #     step=0.1,
            #     key=f"{code}_bb_std",
            # )

            # === MACD ===
            # macd = stock.get("macd", {})
            # macd_fast = st.number_input(
            #     f"{code} MACD Fast",
            #     value=macd.get("fast_period", 12),
            #     step=1,
            #     key=f"{code}_macd_fast",
            # )
            # macd_slow = st.number_input(
            #     f"{code} MACD Slow",
            #     value=macd.get("slow_period", 26),
            #     step=1,
            #     key=f"{code}_macd_slow",
            # )
            # macd_signal = st.number_input(
            #     f"{code} MACD Signal",
            #     value=macd.get("signal_period", 9),
            #     step=1,
            #     key=f"{code}_macd_signal",
            # )

            # # === ADX ===
            # adx = stock.get("adx", {})
            # adx_period = st.number_input(
            #     f"{code} ADX Period",
            #     value=float(adx.get("period", 14)),
            #     step=1.0,
            #     key=f"{code}_adx_period",
            # )
            # adx_thresh = st.number_input(
            #     f"{code} ADX Threshold",
            #     value=adx.get("threshold", 25),
            #     step=1,
            #     key=f"{code}_adx_thresh",
            # )

            # # === MA ===
            # ma = stock.get("moving_averages", {})
            # ma_fast = st.number_input(
            #     f"{code} MA Fast",
            #     value=ma.get("ma_fast", 9),
            #     step=1,
            #     key=f"{code}_ma_fast",
            # )
            # ma_slow = st.number_input(
            #     f"{code} MA Slow",
            #     value=ma.get("ma_slow", 21),
            #     step=1,
            #     key=f"{code}_ma_slow",
            # )

            # # === Inside Bar ===
            # ib = stock.get("inside_bar", {})
            # ib_lookback = st.number_input(
            #     f"{code} Inside Bar Lookback",
            #     value=ib.get("lookback", 1),
            #     step=1,
            #     key=f"{code}_ib_lookback",
            # )

            # # === Candle ===
            # candle = stock.get("candle", {})
            # candle_body = st.number_input(
            #     f"{code} Min Candle Body %",
            #     value=float(candle.get("min_body_percent", 0.7)),
            #     step=0.1,
            #     key=f"{code}_candle",
            # )

            # === Save if any change ===
            if (
                new_support != stock.get("support")
                or new_resistance != stock.get("resistance")
                or new_volume != stock.get("volume_threshold")
                # or bb_period != bb.get("period")
                # or bb_std != bb.get("std_dev")
                # or macd_fast != macd.get("fast_period")
                # or macd_slow != macd.get("slow_period")
                # or macd_signal != macd.get("signal_period")
                # or adx_period != adx.get("period")
                # or adx_thresh != adx.get("threshold")
                # or ma_fast != ma.get("ma_fast")
                # or ma_slow != ma.get("ma_slow")
                # or ib_lookback != ib.get("lookback")
                # or candle_body != candle.get("min_body_percent")
            ):
                stock["support"] = new_support
                stock["resistance"] = new_resistance
                stock["volume_threshold"] = new_volume
                # stock["bollinger"] = {"period": bb_period, "std_dev": bb_std}
                # stock["macd"] = {
                #     "fast_period": macd_fast,
                #     "slow_period": macd_slow,
                #     "signal_period": macd_signal,
                # }
                # stock["adx"] = {"period": adx_period, "threshold": adx_thresh}
                # stock["moving_averages"] = {"ma_fast": ma_fast, "ma_slow": ma_slow}
                # stock["inside_bar"] = {"lookback": ib_lookback}
                # stock["candle"] = {"min_body_percent": candle_body}
                save_config(config)

            # === Breakout logic ===
            signal, current_price, levels, reason = is_breakout(
                df, new_resistance, new_support, stock
            )

            if code not in st.session_state.breakout_shown:
                st.session_state.breakout_shown[code] = False

            now = time.time()
            if signal == "breakout" and not st.session_state.breakout_shown[code]:
                st.session_state.breakout_shown[code] = True
                st.session_state.toast_shown_time[code] = now
                toast(
                    f"🚀 Breakout Alert: {code} at ₹{current_price:.2f} ↑ {new_resistance}",
                    "warning",
                )

            elif signal == "breakdown" and not st.session_state.breakout_shown[code]:
                st.session_state.breakout_shown[code] = True
                st.session_state.toast_shown_time[code] = now
                toast(
                    f"⚠️ Breakdown Alert: {code} at ₹{current_price:.2f} ↓ {new_support}",
                    "error",
                )

            elif st.session_state.breakout_shown.get(code, False):
                elapsed = now - st.session_state.toast_shown_time.get(code, 0)
                if elapsed > 10:
                    st.session_state.breakout_shown[code] = False

            # # === Forecast Button ===
            # if st.button(f"🔮 Forecast {code}", key=f"{code}_forecast_btn"):
            #     with st.spinner("Generating AI-based forecast..."):
            #         forecast_text = forecast_stock(
            #             stock_name=code, csv_file=f"latest_data_{code}.csv", num_rows=10
            #         )
            #         st.markdown("### 🧠 AI Forecast")
            #         st.info(forecast_text)

            # === Periodic Forecast Trigger ===
            last_run_key = f"{code}_last_llm_run"
            now_dt = datetime.now()

            if last_run_key not in st.session_state:
                st.session_state[last_run_key] = now_dt

            last_run_time = st.session_state[last_run_key]
            elapsed_seconds = (now_dt - last_run_time).total_seconds()

            if elapsed_seconds >= 60:
                st.session_state[last_run_key] = now_dt  # update time
                st.caption("🤖 Running AI forecast...")
                time.sleep(3)
                response = forecast_stock(code, f"latest_data_{code}.csv", 2)
                st.info(
                    f"🕒 {now_dt.strftime('%H:%M:%S')} — {response[:300]}{'...' if len(response) > 300 else ''}"
                )


placeholder = st.empty()
while True:
    with placeholder.container():
        render_cards()
    time.sleep(5)
    st.rerun()
