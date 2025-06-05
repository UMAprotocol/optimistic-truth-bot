import requests
import os
from datetime import datetime
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
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
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
        # Try fetching data using the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0][4]  # Close price
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0][4]  # Close price
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            raise

def resolve_market():
    """
    Resolves the market based on the close price of BTCUSDT on Binance.
    """
    # Define the specific times in milliseconds since epoch
    target_time = datetime(2025, 6, 5, 10, 0).timestamp() * 1000  # June 5, 2025, 10:00 UTC
    start_time = int(target_time)
    end_time = int(target_time + 60000)  # Plus one minute

    # Fetch the close price at the specified time
    close_price = fetch_binance_data("BTCUSDT", "1m", start_time, end_time)

    # Check the price against the thresholds
    if float(close_price) >= 250000:
        print("recommendation: p2")  # Yes
    elif float(close_price) < 200000:
        print("recommendation: p1")  # No
    else:
        print("recommendation: p3")  # Unknown/50-50

if __name__ == "__main__":
    resolve_market()