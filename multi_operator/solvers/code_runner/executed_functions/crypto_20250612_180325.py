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
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_eth_price(timestamp):
    """
    Fetches the ETH/USDT price for a specific timestamp using the Binance API.
    Implements a fallback from proxy to primary endpoint.
    """
    params = {
        "symbol": "ETHUSDT",
        "interval": "1h",
        "limit": 1,
        "startTime": timestamp,
        "endTime": timestamp + 3600000  # 1 hour later
    }

    try:
        # Try fetching from the proxy endpoint
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price of the candle
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Close price of the candle
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def resolve_market():
    """
    Resolves the market based on the ETH/USDT price change.
    """
    # Define the specific time for the market resolution
    target_time = datetime(2025, 6, 12, 13, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    target_timestamp = int(target_time.timestamp() * 1000)  # Convert to milliseconds

    # Fetch the closing price of the 1H candle starting at the target time
    closing_price = fetch_eth_price(target_timestamp)

    if closing_price is not None:
        # Compare the closing price with the opening price to determine the market resolution
        if closing_price >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 due to data fetch failure

if __name__ == "__main__":
    resolve_market()