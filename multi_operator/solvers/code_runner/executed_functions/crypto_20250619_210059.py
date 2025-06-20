import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"

def fetch_eth_price(date_time):
    """
    Fetches the ETH/USDT price for a specific hour candle on Binance.
    Args:
        date_time (datetime): The datetime object representing the date and time of interest.
    Returns:
        tuple: (open_price, close_price)
    """
    # Convert datetime to milliseconds since epoch
    timestamp = int(date_time.timestamp() * 1000)

    # Construct the URL and parameters for the API request
    params = {
        "symbol": "ETHUSDT",
        "interval": "1h",
        "startTime": timestamp,
        "endTime": timestamp + 3600000  # 1 hour later
    }

    try:
        # Try fetching from the proxy endpoint first
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Proxy failed, error: {e}, trying primary endpoint.")
        # If proxy fails, fallback to the primary endpoint
        try:
            response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Both proxy and primary endpoints failed, error: {e}")
            return None

    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    else:
        return None

def resolve_market(date_time):
    """
    Resolves the market based on the ETH/USDT prices.
    Args:
        date_time (datetime): The datetime object for the market resolution.
    Returns:
        str: Market resolution recommendation.
    """
    prices = fetch_eth_price(date_time)
    if prices:
        open_price, close_price = prices
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50

# Example usage
if __name__ == "__main__":
    # Define the specific date and time for the market resolution
    market_date_time = datetime(2025, 6, 19, 16, 0)  # June 19, 2025, 4:00 PM ET
    result = resolve_market(market_date_time)
    print(result)