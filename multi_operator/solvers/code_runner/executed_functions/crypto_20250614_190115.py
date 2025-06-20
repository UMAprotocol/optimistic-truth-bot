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
PRIMARY_API_URL = "https://api.binance.com/api/v3"
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
        response = requests.get(f"{PROXY_API_URL}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        print(f"Proxy failed with error: {e}, falling back to primary API.")
        try:
            # Fallback to the primary API endpoint
            response = requests.get(f"{PRIMARY_API_URL}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
            return None

def get_candle_data(symbol, target_datetime):
    """
    Retrieves the closing price of a specific 1-hour candle for the given datetime.
    """
    # Convert datetime to milliseconds
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds

    # Fetch the candle data
    candle_data = fetch_price_data(symbol, "1h", start_time, end_time)
    if candle_data:
        return {
            "open": float(candle_data[1]),
            "close": float(candle_data[4]),
            "high": float(candle_data[2]),
            "low": float(candle_data[3]),
            "volume": float(candle_data[5])
        }
    else:
        return None

def main():
    # Define the target datetime in Eastern Time
    target_datetime_str = "2025-06-14 14:00:00"
    eastern = pytz.timezone("US/Eastern")
    target_datetime = eastern.localize(datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S"))

    # Symbol for the market
    symbol = "BTCUSDT"

    # Get the candle data for the specified time
    candle_data = get_candle_data(symbol, target_datetime)
    if candle_data:
        change_percentage = ((candle_data["close"] - candle_data["open"]) / candle_data["open"]) * 100
        if change_percentage >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 due to data fetch failure

if __name__ == "__main__":
    main()