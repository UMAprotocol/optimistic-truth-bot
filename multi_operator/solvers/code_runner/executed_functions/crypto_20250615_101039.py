import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fallback to the primary endpoint
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data

def get_candle_data(symbol, target_datetime):
    """
    Retrieves the closing price of a 1-hour candle for the specified datetime.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch the candle data
    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        # Extract the closing price from the first candle
        close_price = float(data[0][4])
        return close_price
    else:
        raise ValueError("No data returned from API.")

def main():
    # Define the target datetime in UTC for June 15, 2025, 5 AM ET
    target_datetime_str = "2025-06-15 05:00:00"
    et_timezone = pytz.timezone("US/Eastern")
    utc_timezone = pytz.utc

    # Parse the datetime string into a datetime object
    target_datetime = datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S")
    target_datetime = et_timezone.localize(target_datetime)
    target_datetime_utc = target_datetime.astimezone(utc_timezone)

    # Symbol for the market
    symbol = "BTCUSDT"

    try:
        # Get the closing price of the 1-hour candle starting at the target datetime
        closing_price_start = get_candle_data(symbol, target_datetime_utc)
        # Get the closing price of the previous 1-hour candle
        closing_price_end = get_candle_data(symbol, target_datetime_utc + timedelta(hours=1))

        # Determine the market resolution based on the price change
        if closing_price_end >= closing_price_start:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        print(f"Error fetching data: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    main()