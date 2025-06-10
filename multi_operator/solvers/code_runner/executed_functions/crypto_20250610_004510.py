import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, start_time, end_time):
    """
    Fetches historical data from Binance for a specific symbol within a given time range.
    Tries the proxy endpoint first, then falls back to the primary endpoint if necessary.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Maximum allowed by Binance
        "startTime": start_time,
        "endTime": end_time
    }

    try:
        # Try fetching data using the proxy endpoint
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")

    try:
        # Fallback to the primary endpoint if proxy fails
        response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Primary endpoint also failed: {e}")
        return None

def check_xrp_dip_to_price(target_price, start_date, end_date):
    """
    Checks if XRP dipped to a certain price within a specified date range.
    """
    # Convert dates to timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))

    start_ts = int(start_dt.timestamp() * 1000)
    end_ts = int(end_dt.timestamp() * 1000)

    # Fetch data from Binance
    data = fetch_binance_data("XRPUSDT", start_ts, end_ts)

    if data:
        for candle in data:
            low_price = float(candle[3])  # Low price is the fourth element in the list
            if low_price <= target_price:
                return True
    return False

def main():
    """
    Main function to determine if XRP dipped to $1.90 in May 2025.
    """
    result = check_xrp_dip_to_price(1.90, "2025-05-01", "2025-05-31")
    if result:
        print("recommendation: p2")  # Yes, it dipped to $1.90 or lower
    else:
        print("recommendation: p1")  # No, it did not dip to $1.90

if __name__ == "__main__":
    main()