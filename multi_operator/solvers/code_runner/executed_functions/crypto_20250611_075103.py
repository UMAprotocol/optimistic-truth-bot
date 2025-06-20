import requests
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

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
        # Try fetching data using the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0][4]  # Close price
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0][4]  # Close price
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            raise

def main():
    # Specific event details
    symbol = "BTCUSDT"
    interval = "1m"
    target_time_utc = datetime(2025, 6, 11, 7, 0, tzinfo=timezone.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)
    end_time_ms = start_time_ms + 60000  # 1 minute later

    try:
        close_price = fetch_binance_data(symbol, interval, start_time_ms, end_time_ms)
        close_price = float(close_price)
        print(f"Close price at {target_time_utc}: {close_price} USDT")
        
        # Determine resolution based on the close price
        if close_price >= 225000:
            print("recommendation: p2")  # Yes
        else:
            print("recommendation: p1")  # No
    except Exception as e:
        print(f"Failed to fetch or process data: {str(e)}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()