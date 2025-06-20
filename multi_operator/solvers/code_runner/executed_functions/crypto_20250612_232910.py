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
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data

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
        # Extract the closing price from the first candle returned
        close_price = float(data[0][4])
        return close_price
    else:
        raise ValueError("No data returned from the API.")

def main():
    # Define the target date and time for the candle
    target_date_str = "2025-06-12"
    target_time_str = "18:00:00"
    timezone_str = "US/Eastern"

    # Convert string to datetime object in the specified timezone
    tz = pytz.timezone(timezone_str)
    target_datetime = datetime.strptime(target_date_str + " " + target_time_str, "%Y-%m-%d %H:%M:%S")
    target_datetime = tz.localize(target_datetime)

    # Convert to UTC
    target_datetime_utc = target_datetime.astimezone(pytz.utc)

    # Symbol for the market
    symbol = "BTCUSDT"

    try:
        # Get the closing price of the target candle
        closing_price = get_candle_data(symbol, target_datetime_utc)
        print(f"Closing price for the candle starting at {target_datetime_utc} UTC is {closing_price}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()