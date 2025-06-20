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
    headers = {
        "X-MBX-APIKEY": BINANCE_API_KEY
    }

    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()

def get_candle_data(symbol, target_datetime):
    """
    Retrieves the closing price of a specific 1-hour candle for the given symbol at the target datetime.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        # Extract the close price from the first candle returned
        close_price = float(data[0][4])
        return close_price
    else:
        raise ValueError("No data returned for the specified time and symbol.")

def main():
    # Define the target date and time
    target_date_str = "2025-06-17"
    target_time_str = "11:00:00"
    timezone_str = "US/Eastern"
    symbol = "BTCUSDT"

    # Convert target date and time to datetime object
    target_datetime = datetime.strptime(f"{target_date_str} {target_time_str}", "%Y-%m-%d %H:%M:%S")
    target_datetime = pytz.timezone(timezone_str).localize(target_datetime)

    # Get the closing price of the 1-hour candle starting at the target datetime
    try:
        closing_price = get_candle_data(symbol, target_datetime)
        print(f"Closing price for {symbol} at {target_datetime} was {closing_price}")
    except Exception as e:
        print(f"Error fetching price data: {e}")

if __name__ == "__main__":
    main()