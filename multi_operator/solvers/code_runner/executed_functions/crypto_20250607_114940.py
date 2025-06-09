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
            return None

def resolve_market():
    """
    Resolves the market based on the close price of BTCUSDT on Binance at a specific time.
    """
    # Specific date and time for the query
    target_datetime = datetime(2025, 6, 7, 6, 0, tzinfo=timezone.utc)
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later

    # Fetch the close price
    close_price = fetch_binance_data("BTCUSDT", "1m", start_time, end_time)
    
    if close_price is None:
        print("recommendation: p4")  # Unable to fetch data
    else:
        close_price = float(close_price)
        if close_price >= 225000:
            print("recommendation: p2")  # Yes, price is higher than or equal to 225,000 USDT
        else:
            print("recommendation: p1")  # No, price is lower than 225,000 USDT

if __name__ == "__main__":
    resolve_market()