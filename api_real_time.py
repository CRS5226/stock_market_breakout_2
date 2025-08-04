import os
import time
from dotenv import load_dotenv
from breeze_connect import BreezeConnect

# Load environment variables
load_dotenv()

API_KEY = os.getenv("BREEZE_API_KEY")
API_SECRET = os.getenv("BREEZE_API_SECRET")
SESSION_TOKEN = os.getenv("BREEZE_SESSION_TOKEN")

# Initialize Breeze
breeze = BreezeConnect(api_key=API_KEY)

# Authenticate session
try:
    breeze.generate_session(api_secret=API_SECRET, session_token=SESSION_TOKEN)
    print("[✓] Session generated successfully.")
except Exception as e:
    print(f"[!] Session generation failed: {e}")
    exit()


# Define callback to handle incoming ticks
def on_ticks(ticks):
    print("[📡] Tick Received:", ticks)


# Assign the callback
breeze.on_ticks = on_ticks

# Connect to WebSocket
try:
    breeze.ws_connect()
    print("[✓] WebSocket connection established.")
except Exception as e:
    print(f"[!] Failed to connect to WebSocket: {e}")
    exit()

# Subscribe to NIFTY feed
try:
    breeze.subscribe_feeds(
        exchange_code="NSE",
        # stock_code="NIFTY",
        stock_code="WIPRO",
        product_type="cash",
        get_market_depth=False,
        get_exchange_quotes=True,
    )
    print("[*] Subscribed to live feed.")
except Exception as e:
    print(f"[!] Feed subscription failed: {e}")
    exit()

# Keep the script running to receive live ticks
print("[⏳] Waiting for live tick data...\nPress Ctrl+C to stop.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n[✋] Exiting on user interrupt...")
    breeze.ws_disconnect()
    print("[✓] WebSocket disconnected.")
