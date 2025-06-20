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
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def get_price_change(symbol, target_datetime):
    """
    Calculates the price change percentage for the specified symbol at the given datetime.
    """
    # Convert datetime to the correct format for the API call
    start_time = int(target_datetime.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later

    # Fetch data
    data = fetch_binance_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change_percent = ((close_price - open_price) / open_price) * 100
        return price_change_percent
    else:
        return None

def main():
    """
    Main function to determine if the Bitcoin price went up or down.
    """
    target_datetime = datetime(2025, 6, 15, 4, 0, tzinfo=pytz.timezone("US/Eastern"))
    symbol = "BTCUSDT"
    price_change = get_price_change(symbol, target_datetime)

    if price_change is None:
        print("recommendation: p3")  # Unknown or data not available
    elif price_change >= 0:
        print("recommendation: p2")  # Price went up
    else:
        print("recommendation: p1")  # Price went down

if __name__ == "__main__":
    main()