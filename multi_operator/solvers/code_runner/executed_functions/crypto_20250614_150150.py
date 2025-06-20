import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_data_from_binance(symbol, interval, start_time, end_time):
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
    headers = {
        "X-MBX-APIKEY": BINANCE_API_KEY
    }

    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def get_price_change(symbol, start_time):
    """
    Determines if the price of a cryptocurrency has gone up or down based on the opening and closing prices.
    """
    # Convert datetime to milliseconds since epoch
    start_time_ms = int(start_time.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later

    data = fetch_data_from_binance(symbol, "1h", start_time_ms, end_time_ms)
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 if no data is available

def main():
    # Example date and time for the market resolution
    market_date_str = "2025-06-14 10:00:00"
    market_date = datetime.strptime(market_date_str, "%Y-%m-%d %H:%M:%S")
    
    # Symbol for the market
    symbol = "BTCUSDT"
    
    # Get the price change result
    result = get_price_change(symbol, market_date)
    
    # Print the recommendation based on the price change
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()