import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

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
        if data:
            return data[0][3]  # Low price
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{PRIMARY_URL}/klines", params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0][3]  # Low price

def check_price_dip_to_nine():
    """
    Checks if the price of HYPE/USDC dipped to $9.000 or lower between May 7, 2025, and May 31, 2025.
    """
    symbol = "HYPEUSDC"
    start_date = datetime(2025, 5, 7, 0, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    end_date = datetime(2025, 5, 31, 23, 59, 59, tzinfo=pytz.timezone("US/Eastern"))
    start_time = int(start_date.timestamp() * 1000)
    end_time = int(end_date.timestamp() * 1000)

    try:
        low_price = get_data(symbol, start_time, end_time)
        if low_price and float(low_price) <= 9.0:
            return "recommendation: p2"  # Yes, it dipped to $9 or lower
        else:
            return "recommendation: p1"  # No, it did not dip to $9 or lower
    except Exception as e:
        print(f"Error checking price dip: {e}")
        return "recommendation: p3"  # Unknown/50-50 due to error

def main():
    result = check_price_dip_to_nine()
    print(result)

if __name__ == "__main__":
    main()