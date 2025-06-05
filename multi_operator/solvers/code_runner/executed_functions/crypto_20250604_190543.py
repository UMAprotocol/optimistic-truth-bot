import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_data_from_binance(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Maximum allowed by Binance
        "startTime": start_time,
        "endTime": end_time
    }

    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def check_sui_price_threshold(start_date, end_date, threshold_price):
    """
    Checks if the SUI/USDT price reached the threshold price within the given date range.
    """
    # Convert dates to UTC timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d %H:%M"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d %H:%M"))

    start_ts = int(start_dt.timestamp() * 1000)
    end_ts = int(end_dt.timestamp() * 1000)

    # Fetch data from Binance
    data = fetch_data_from_binance("SUIUSDT", start_ts, end_ts)

    # Check if any candle high price meets or exceeds the threshold
    for candle in data:
        high_price = float(candle[2])  # High price is the third element in each candle
        if high_price >= threshold_price:
            return True

    return False

def main():
    """
    Main function to determine if the SUI/USDT price reached $4.6 in May 2025.
    """
    result = check_sui_price_threshold("2025-05-07 00:00", "2025-05-31 23:59", 4.6)
    if result:
        print("recommendation: p2")  # Yes, price reached $4.6 or higher
    else:
        print("recommendation: p1")  # No, price did not reach $4.6

if __name__ == "__main__":
    main()