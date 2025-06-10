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
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, start_time, end_time):
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
        # Try fetching data using the proxy endpoint
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def check_bitcoin_price_threshold(start_date, end_date, threshold):
    """
    Checks if Bitcoin price reached a certain threshold within a given date range.
    """
    # Convert dates to UTC timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d %H:%M"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d %H:%M"))

    start_timestamp = int(start_dt.timestamp() * 1000)
    end_timestamp = int(end_dt.timestamp() * 1000)

    # Fetch data from Binance
    data = fetch_binance_data("BTCUSDT", start_timestamp, end_timestamp)

    # Check if any candle high price meets or exceeds the threshold
    for candle in data:
        high_price = float(candle[2])  # High price is the third element in each candle
        if high_price >= threshold:
            return True

    return False

def main():
    """
    Main function to determine if Bitcoin reached $125k in May 2025.
    """
    result = check_bitcoin_price_threshold("2025-05-01 00:00", "2025-05-31 23:59", 125000)
    if result:
        print("recommendation: p2")  # Bitcoin reached $125k, resolve to "Yes"
    else:
        print("recommendation: p1")  # Bitcoin did not reach $125k, resolve to "No"

if __name__ == "__main__":
    main()