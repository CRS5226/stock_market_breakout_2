# indicator.py

import pandas as pd
import numpy as np


def add_indicators(df, config):
    try:
        # Moving Averages
        ma_fast = config.get("moving_averages", {}).get("ma_fast", 5)
        ma_slow = config.get("moving_averages", {}).get("ma_slow", 20)
        df["MA_Fast"] = df["Close"].rolling(window=ma_fast).mean()
        df["MA_Slow"] = df["Close"].rolling(window=ma_slow).mean()

        # Bollinger Bands
        bb_cfg = config.get("bollinger", {})
        period = bb_cfg.get("period", 20)
        std_dev = bb_cfg.get("std_dev", 2)
        df["BB_Mid"] = df["Close"].rolling(window=period).mean()
        df["BB_Std"] = df["Close"].rolling(window=period).std()
        df["BB_Upper"] = df["BB_Mid"] + (df["BB_Std"] * std_dev)
        df["BB_Lower"] = df["BB_Mid"] - (df["BB_Std"] * std_dev)

        # MACD
        macd_cfg = config.get("macd", {})
        fast = macd_cfg.get("fast_period", 12)
        slow = macd_cfg.get("slow_period", 26)
        signal_period = macd_cfg.get("signal_period", 9)
        ema_fast = df["Close"].ewm(span=fast, adjust=False).mean()
        ema_slow = df["Close"].ewm(span=slow, adjust=False).mean()
        df["MACD"] = ema_fast - ema_slow
        df["MACD_Signal"] = df["MACD"].ewm(span=signal_period, adjust=False).mean()
        df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]

        # ADX
        adx_period = config.get("adx", {}).get("period", 14)
        df = compute_adx(df, adx_period)

        return df

    except Exception as e:
        print(f"[Indicator Error] Failed to compute indicators: {e}")
        raise e


def compute_adx(df, period):
    df["UpMove"] = df["High"].diff()
    df["DownMove"] = df["Low"].diff()
    df["+DM"] = np.where(
        (df["UpMove"] > df["DownMove"]) & (df["UpMove"] > 0), df["UpMove"], 0
    )
    df["-DM"] = np.where(
        (df["DownMove"] > df["UpMove"]) & (df["DownMove"] > 0), df["DownMove"], 0
    )

    df["TR_tmp1"] = df["High"] - df["Low"]
    df["TR_tmp2"] = abs(df["High"] - df["Close"].shift(1))
    df["TR_tmp3"] = abs(df["Low"] - df["Close"].shift(1))
    df["TR"] = df[["TR_tmp1", "TR_tmp2", "TR_tmp3"]].max(axis=1)

    df["+DI"] = 100 * (
        df["+DM"].ewm(span=period, adjust=False).mean()
        / df["TR"].ewm(span=period, adjust=False).mean()
    )
    df["-DI"] = 100 * (
        df["-DM"].ewm(span=period, adjust=False).mean()
        / df["TR"].ewm(span=period, adjust=False).mean()
    )
    df["DX"] = 100 * (abs(df["+DI"] - df["-DI"]) / (df["+DI"] + df["-DI"]))
    df["ADX"] = df["DX"].ewm(span=period, adjust=False).mean()

    return df


def is_breakout(df, resistance, support, config):
    if len(df) < 5:
        return None, None, None, "Insufficient data"

    current = df.iloc[-1]

    close = current["Close"]
    # volume = current["Volume"]
    # vol_thresh = config.get("volume_threshold", 0)

    # Breakout logic
    if close > resistance:
        reason = f"📈 Breakout: Close ({close:.2f}) > Resistance ({resistance:.2f})"

        # if volume < vol_thresh:
        #     reason += " | Low Volume"
        # else:
        #     reason += " | Volume OK"

        # if close > current["BB_Upper"]:
        #     reason += " | BB confirms"
        # else:
        #     reason += " | BB no confirm"

        # if current["ADX"] < config["adx"]["threshold"]:
        #     reason += f" | ADX={round(current['ADX'], 1)} < threshold"
        # else:
        #     reason += f" | ADX={round(current['ADX'], 1)} confirms"

        return "breakout", close, resistance, reason

    # Breakdown logic
    elif close < support:
        reason = f"📉 Breakdown: Close ({close:.2f}) < Support ({support:.2f})"

        # if volume < vol_thresh:
        #     reason += " | Low Volume"
        # else:
        #     reason += " | Volume OK"

        # if close < current["BB_Lower"]:
        #     reason += " | BB confirms"
        # else:
        #     reason += " | BB no confirm"

        # if current["ADX"] < config["adx"]["threshold"]:
        #     reason += f" | ADX={round(current['ADX'], 1)} < threshold"
        # else:
        #     reason += f" | ADX={round(current['ADX'], 1)} confirms"

        # return "breakdown", close, support, reason

    return None, None, None, "No breakout/breakdown"
