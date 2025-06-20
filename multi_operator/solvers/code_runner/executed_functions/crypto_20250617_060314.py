import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_ENDPOINT = "https://api.binance.com/api/v3/klines"
PROXY_API_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy endpoint.
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
        response = requests.get(PROXY_API_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def get_candle_data(symbol, target_datetime):
    """
    Retrieves the closing price of a specific 1-hour candle for the given datetime.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds

    # Fetch the candle data
    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        # Extract the closing price from the first candle
        close_price = float(data[0][4])
        return close_price
    else:
        raise ValueError("No data returned from API.")

def main():
    # Define the target date and time for the candle
    target_date_str = "2025-06-17"
    target_time_str = "01:00:00"
    timezone_str = "US/Eastern"

    # Convert the target time to UTC
    tz = pytz.timezone(timezone_str)
    target_datetime_local = datetime.strptime(f"{target_date_str} {target_time_str}", "%Y-%m-%d %H:%M:%S")
    target_datetime_local = tz.localize(target_datetime_local)
    target_datetime_utc = target_datetime_local.astimezone(pytz.utc)

    # Symbol for the market
    symbol = "BTCUSDT"

    # Get the closing price of the 1-hour candle starting at the target time
    try:
        closing_price_start = get_candle_data(symbol, target_datetime_utc)
        print(f"Closing price at the start of the candle: {closing_price_start}")

        # Get the closing price of the 1-hour candle one hour later
        closing_price_end = get_candle_data(symbol, target_datetime_utc + timedelta(hours=1))
        print(f"Closing price at the end of the candle: {closing_price_end}")

        # Determine the resolution based on the price change
        if closing_price_end >= closing_price_start:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        print(f"Error fetching data: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    main()