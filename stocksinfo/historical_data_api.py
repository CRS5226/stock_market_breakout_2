import os
from datetime import datetime
from breeze_connect import BreezeConnect
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# API credentials
API_KEY = os.getenv("BREEZE_API_KEY")
API_SECRET = os.getenv("BREEZE_API_SECRET")
SESSION_TOKEN = os.getenv("BREEZE_SESSION_TOKEN")

# Initialize Breeze
breeze = BreezeConnect(api_key=API_KEY)

# Authenticate session
try:
    breeze.generate_session(api_secret=API_SECRET, session_token=SESSION_TOKEN)
    print("[✓] Session authentication successful.")
except Exception as e:
    print(f"[!] Error during session generation: {e}")
    exit()

# Stocks to fetch: (stock_code, expiry_date)
stocks = [
    "TRENT",
    "ASIPAI",
    "HINLEV",
    "NESIND",
    "HERHON",
    "ITC",
    "EICMOT",
    "KOTMAH",
    "BAAUTO",
    "RELIND",
    "POWGRI",
    "JIOFIN",
    "TATGLO",
    "HDFBAN",
    "AXIBAN",
    "BAJFI",
    "ICIBAN",
    "TITIND",
    "NTPC",
    "TCS",
]

# Common parameters (updated to 1st August 2025 full day session)
from_date = "2025-08-01T09:15:00.000Z"
to_date = "2025-08-01T15:30:00.000Z"
expiry_date = "2025-08-28T07:00:00.000Z"

# Create output folder
os.makedirs("stock_csv", exist_ok=True)

for stock_code in stocks:
    try:
        print(f"[*] Fetching data for: {stock_code}")

        data = breeze.get_historical_data(
            interval="1minute",
            from_date=from_date,
            to_date=to_date,
            stock_code=stock_code,
            exchange_code="NFO",
            product_type="futures",
            expiry_date=expiry_date,
            right="others",
            strike_price="0",
        )

        if data and "Success" in data and isinstance(data["Success"], list):
            df = pd.DataFrame(data["Success"])
            print(f"[✓] Retrieved {len(df)} records for {stock_code}")

            file_path = f"stock_csv/latest_data_{stock_code}.csv"
            df.to_csv(file_path, index=False)
            print(f"[✓] Saved to {file_path}")
        else:
            print(f"[!] No valid data for {stock_code} or unexpected structure.")

    except Exception as e:
        print(f"[!] Error fetching data for {stock_code}: {e}")
