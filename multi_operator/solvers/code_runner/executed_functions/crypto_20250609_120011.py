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
    Fetches price data from Binance API using a proxy with a fallback to the primary API.
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
            return data[0][4]  # Close price of the candle
    except Exception as e:
        print(f"Proxy failed with error: {e}. Trying primary API endpoint.")
        try:
            # Fallback to the primary API endpoint if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0][4]  # Close price of the candle
        except Exception as e:
            print(f"Primary API also failed with error: {e}.")
            return None

def resolve_market():
    """
    Resolves the market based on the price change of BTC/USDT on Binance.
    """
    # Define the specific time and date for the market resolution
    target_datetime = datetime(2025, 6, 9, 7, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    start_time = int(target_datetime.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later

    # Fetch the closing price at the start and end of the 1-hour interval
    start_price = fetch_price_data("BTCUSDT", "1h", start_time, start_time + 60000)
    end_price = fetch_price_data("BTCUSDT", "1h", end_time - 60000, end_time)

    if start_price is None or end_price is None:
        print("recommendation: p4")  # Unable to fetch data
    else:
        start_price = float(start_price)
        end_price = float(end_price)
        # Determine if the price went up or down
        if end_price >= start_price:
            print("recommendation: p2")  # Market resolves to "Up"
        else:
            print("recommendation: p1")  # Market resolves to "Down"

if __name__ == "__main__":
    resolve_market()