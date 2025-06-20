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

def fetch_data_from_binance(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary request fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
    }
    
    try:
        # Try fetching from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy failed with error: {e}, trying primary API endpoint.")
        # Fallback to the primary API endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
            return None

def get_candle_data(symbol, target_datetime):
    """
    Converts the target datetime to milliseconds and fetches the candle data for that specific minute.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later
    
    data = fetch_data_from_binance(symbol, "1m", start_time, end_time)
    if data and len(data) > 0:
        # Extract the closing price from the first (and only) candle
        close_price = float(data[0][4])
        return close_price
    else:
        return None

def main():
    # Define the target datetime for the candle (June 16, 2025, 1 AM ET)
    target_datetime = datetime(2025, 6, 16, 1, 0, 0)
    
    # Fetch the closing price for BTC/USDT at the specified time
    close_price_start = get_candle_data("BTCUSDT", target_datetime)
    close_price_end = get_candle_data("BTCUSDT", target_datetime + timedelta(hours=1))
    
    if close_price_start is None or close_price_end is None:
        print("recommendation: p4")  # Unable to fetch data
    else:
        # Determine if the price went up or down
        if close_price_end >= close_price_start:
            print("recommendation: p2")  # Price went up
        else:
            print("recommendation: p1")  # Price went down

if __name__ == "__main__":
    main()