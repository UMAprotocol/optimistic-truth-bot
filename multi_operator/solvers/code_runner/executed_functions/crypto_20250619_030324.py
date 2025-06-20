import requests
import os
from datetime import datetime, timedelta
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
        date_time (datetime): The datetime object representing the specific hour for the candle.
    Returns:
        tuple: (open_price, close_price)
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(date_time.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Construct the URL and parameters for the API request
    params = {
        "symbol": "ETHUSDT",
        "interval": "1h",
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
    }

    try:
        # Try fetching from the proxy endpoint first
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Proxy failed with error: {e}, trying primary endpoint.")
        # Fallback to the primary endpoint if proxy fails
        response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params)
        response.raise_for_status()
        data = response.json()

    # Extract open and close prices from the data
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    else:
        raise ValueError("No data returned from API.")

def resolve_market(date_str):
    """
    Resolves the market based on the ETH/USDT prices at the specified date and time.
    Args:
        date_str (str): The date and time string in the format "YYYY-MM-DD HH:MM TZ".
    Returns:
        str: The resolution of the market ("Up" or "Down").
    """
    # Parse the date string to a datetime object
    market_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M %Z")
    
    # Fetch the open and close prices
    open_price, close_price = fetch_eth_price(market_time)
    
    # Determine if the price went up or down
    if close_price >= open_price:
        return "recommendation: p2"  # Up
    else:
        return "recommendation: p1"  # Down

# Example usage
if __name__ == "__main__":
    # The specific date and time for the market resolution
    market_date_str = "2025-06-18 22:00 ET"
    try:
        result = resolve_market(market_date_str)
        print(result)
    except Exception as e:
        print(f"Error resolving market: {e}")
        print("recommendation: p4")  # Unable to resolve