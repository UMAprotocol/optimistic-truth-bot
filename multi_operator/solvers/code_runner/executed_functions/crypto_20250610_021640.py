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
    
    Args:
        symbol (str): The symbol to fetch data for.
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    
    Returns:
        json: The API response.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Maximum allowed by Binance for one request
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def check_doge_price_threshold(start_date, end_date, threshold=0.30):
    """
    Checks if the price of Dogecoin ever reaches or exceeds the threshold within the given date range.
    
    Args:
        start_date (str): Start date in 'YYYY-MM-DD' format.
        end_date (str): End date in 'YYYY-MM-DD' format.
        threshold (float): Price threshold to check.
    
    Returns:
        str: 'p1' if the price never reaches the threshold, 'p2' if it does.
    """
    # Convert dates to UTC timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))
    
    start_ts = int(start_dt.timestamp() * 1000)
    end_ts = int(end_dt.timestamp() * 1000)
    
    # Fetch data in chunks (due to API limit constraints)
    current_ts = start_ts
    while current_ts < end_ts:
        data = fetch_data_from_binance("DOGEUSDT", current_ts, min(current_ts + 86400000, end_ts))  # 1 day in milliseconds
        for candle in data:
            if float(candle[2]) >= threshold:  # candle[2] is the 'High' price in the candlestick data
                return "p2"  # Yes, price reached or exceeded the threshold
        current_ts += 86400000  # Move to the next day
    
    return "p1"  # No, price never reached the threshold

def main():
    result = check_doge_price_threshold("2025-05-01", "2025-05-31")
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()