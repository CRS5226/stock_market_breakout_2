# groq_forecast.py

import os
import pandas as pd
from dotenv import load_dotenv
from groq import Groq
from datetime import datetime

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def forecast_stock(stock_name: str, csv_file: str, num_rows: int = 10) -> str:
    if not os.path.exists(csv_file):
        return f"❌ CSV file not found: {csv_file}"

    df = pd.read_csv(csv_file)
    if df.shape[0] < num_rows:
        return f"❌ Not enough rows in file (found {df.shape[0]}, expected {num_rows})"

    latest_df = df.tail(num_rows)
    latest_csv = latest_df.to_csv(index=False)

    prompt = f"""You are a professional stock analyst. Analyze the following real-time stock data and determine the next trading action.

Please provide:
1. A clear recommendation (e.g., Buy, Sell, Hold, Set Stop Loss, Wait)
2. A target price (if applicable)
3. Key reasons based on Close price trend, Volume, Support/Resistance, Bollinger Bands, ADX, and breakout/breakdown patterns
4. Risk Level (Low, Medium, High)

Only respond with concise and precise analysis.

Here is the most recent data:
{latest_csv}"""

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a stock market expert."},
                {"role": "user", "content": prompt},
            ],
            model="allam-2-7b",
            temperature=0.4,
            max_tokens=512,
            top_p=1.0,
            stream=False,
        )

        output_text = response.choices[0].message.content.strip()

        # Save response to a timestamped CSV row
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_path = f"./forecast/LLM_data_{stock_name}.csv"
        df_row = pd.DataFrame([[timestamp, output_text]], columns=["Time", "Forecast"])

        if os.path.exists(save_path):
            df_row.to_csv(save_path, mode="a", index=False, header=False)
        else:
            df_row.to_csv(save_path, index=False)

        return output_text

    except Exception as e:
        return f"❌ Error during forecast: {str(e)}"
