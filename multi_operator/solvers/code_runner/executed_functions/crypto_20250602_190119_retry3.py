import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": "1h",
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def get_candle_data(symbol, target_datetime):
    """
    Retrieves the closing price of the 1-hour candle for the specified datetime.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    data = fetch_price_data(symbol, start_time, end_time)
    if data and len(data) > 0:
        # Extract the close price from the first candle returned
        close_price = float(data[0][4])
        return close_price
    else:
        raise ValueError("No data available for the specified time.")

def main():
    # Define the target date and time
    target_datetime = datetime(2025, 6, 2, 14, 0)  # June 2, 2025, 2:00 PM ET
    symbol = "BTCUSDT"

    try:
        # Get the closing price of the 1-hour candle starting at 2:00 PM ET
        closing_price_start = get_candle_data(symbol, target_datetime)
        # Get the closing price of the 1-hour candle starting at 3:00 PM ET
        closing_price_end = get_candle_data(symbol, target_datetime + timedelta(hours=1))

        # Determine the market resolution based on the price change
        if closing_price_end >= closing_price_start:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        print(f"Error occurred: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    main()