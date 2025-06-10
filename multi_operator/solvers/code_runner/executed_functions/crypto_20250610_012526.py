import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_URL = "https://api.binance.com/api/v3"

def get_data(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    headers = {
        "X-MBX-APIKEY": BINANCE_API_KEY
    }

    try:
        # First try the proxy endpoint
        response = requests.get(f"{PROXY_URL}/klines", params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            return float(data[0][3])  # Low price
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{PRIMARY_URL}/klines", params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            return float(data[0][3])  # Low price

    return None

def check_price_dip(symbol, start_date, end_date, target_price):
    """
    Checks if the price of a cryptocurrency dipped to or below a target price between two dates.
    """
    # Convert dates to timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d %H:%M"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d %H:%M"))
    start_ts = int(start_dt.timestamp() * 1000)
    end_ts = int(end_dt.timestamp() * 1000)

    # Check every minute between start and end dates
    while start_ts < end_ts:
        low_price = get_data(symbol, start_ts, start_ts + 60000)  # 1 minute in milliseconds
        if low_price is not None and low_price <= target_price:
            return True
        start_ts += 60000

    return False

def main():
    """
    Main function to determine if the price of Housecoin dipped to $0.020 or lower.
    """
    symbol = "HOUSEUSDT"
    start_date = "2025-05-07 15:00"
    end_date = "2025-05-31 23:59"
    target_price = 0.020

    if check_price_dip(symbol, start_date, end_date, target_price):
        print("recommendation: p2")  # Yes, it dipped to $0.020 or lower
    else:
        print("recommendation: p1")  # No, it did not dip to $0.020 or lower

if __name__ == "__main__":
    main()