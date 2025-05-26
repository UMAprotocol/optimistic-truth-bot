import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price(symbol, date_str, time_str, timezone_str):
    """
    Fetch the close price of a cryptocurrency at a specific time from Binance.
    """
    # Convert local time to UTC
    local_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    local_tz = pytz.timezone(timezone_str)
    local_dt = local_tz.localize(local_dt)
    utc_dt = local_dt.astimezone(pytz.utc)
    start_time = int(utc_dt.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later in milliseconds

    # Construct the request URL
    params = {
        "symbol": symbol,
        "interval": "1m",
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
    }

    try:
        # Try fetching from the proxy endpoint first
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        print(f"Proxy failed, trying primary endpoint: {e}")
        # Fallback to the primary endpoint
        try:
            response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Close price
        except Exception as e:
            print(f"Both proxy and primary endpoints failed: {e}")
            return None

def resolve_market():
    """
    Resolve the market based on the close prices of SOLUSDT on Binance.
    """
    symbol = "SOLUSDT"
    timezone_str = "US/Eastern"
    date1 = "2025-05-25"
    date2 = "2025-05-26"
    time_str = "12:00"

    price1 = fetch_price(symbol, date1, time_str, timezone_str)
    price2 = fetch_price(symbol, date2, time_str, timezone_str)

    if price1 is None or price2 is None:
        return "recommendation: p4"  # Unable to fetch prices

    if price1 < price2:
        return "recommendation: p2"  # Up
    elif price1 > price2:
        return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # 50-50

if __name__ == "__main__":
    result = resolve_market()
    print(result)