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
    try:
        # First try the proxy endpoint
        response = requests.get(f"{PROXY_URL}/klines", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{PRIMARY_URL}/klines", params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def check_price_dip(symbol, start_date, end_date, target_price):
    """
    Checks if the price of a cryptocurrency dipped to or below a target price between two dates.
    """
    # Convert dates to UTC timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d %H:%M"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d %H:%M"))
    start_ts = int(start_dt.timestamp() * 1000)
    end_ts = int(end_dt.timestamp() * 1000)

    # Fetch data
    data = get_data(symbol, start_ts, end_ts)
    if data and len(data) > 0:
        # Check if any low price is at or below the target price
        for candle in data:
            low_price = float(candle[3])  # Low price is the fourth element in the list
            if low_price <= target_price:
                return True
    return False

def main():
    """
    Main function to determine if the price of Housecoin dipped to $0.025 or lower.
    """
    symbol = "HOUSEUSDT"
    start_date = "2025-05-07 15:00"
    end_date = "2025-05-31 23:59"
    target_price = 0.025

    if check_price_dip(symbol, start_date, end_date, target_price):
        print("recommendation: p2")  # Yes, price dipped to $0.025 or lower
    else:
        print("recommendation: p1")  # No, price did not dip to $0.025 or lower

if __name__ == "__main__":
    main()