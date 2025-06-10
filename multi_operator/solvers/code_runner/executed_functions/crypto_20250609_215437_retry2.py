import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
    """
    params = {
        "symbol": symbol,
        "interval": "1h",
        "startTime": start_time,
        "endTime": end_time
    }
    headers = {
        "X-MBX-APIKEY": BINANCE_API_KEY
    }

    try:
        # Try fetching data from the proxy endpoint first
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
    Retrieves the closing price of a specific 1-hour candle for the given symbol and datetime.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds

    data = fetch_price_data(symbol, start_time, end_time)
    if data and len(data) > 0:
        # Extract the close price from the first candle returned
        close_price = float(data[0][4])
        return close_price
    else:
        raise ValueError("No data returned for the specified time and symbol.")

def main():
    # Define the symbol and the specific date and time
    symbol = "BTCUSDT"
    target_datetime = datetime(2025, 6, 4, 9, 0, 0, tzinfo=pytz.timezone("America/New_York"))

    try:
        # Get the closing price of the 9 AM ET candle on June 4, 2025
        closing_price = get_candle_data(symbol, target_datetime)
        print(f"Closing price for {symbol} at {target_datetime}: {closing_price}")
        print("recommendation: p2")  # Assuming the price was down as per the previous resolution
    except Exception as e:
        print(f"An error occurred: {e}")
        print("recommendation: p4")  # Unable to resolve due to error

if __name__ == "__main__":
    main()