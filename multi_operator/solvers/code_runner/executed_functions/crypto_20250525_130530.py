import requests
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price(symbol, date_str, hour=12, minute=0, timezone_str="US/Eastern"):
    """
    Fetches the closing price of a cryptocurrency pair from Binance at a specific time.
    """
    # Convert local time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S")
    local_dt = tz.localize(local_time)
    utc_dt = local_dt.astimezone(pytz.utc)
    timestamp = int(utc_dt.timestamp() * 1000)  # Convert to milliseconds

    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": timestamp,
        "endTime": timestamp + 60000  # 1 minute later
    }

    try:
        # Try fetching from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price
    except Exception as e:
        print(f"Proxy failed, error: {e}, trying primary API...")
        # Fallback to the primary API endpoint
        response = requests.get(PRIMARY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price

def resolve_market():
    """
    Resolves the market based on the closing prices of ETH/BTC on two specific dates.
    """
    symbol = "ETHBTC"
    close_price_may23 = fetch_price(symbol, "2025-05-23", 12, 0, "US/Eastern")
    close_price_may24 = fetch_price(symbol, "2025-05-24", 12, 0, "US/Eastern")

    if close_price_may23 < close_price_may24:
        return "recommendation: p2"  # Up
    elif close_price_may23 > close_price_may24:
        return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # 50-50

if __name__ == "__main__":
    result = resolve_market()
    print(result)