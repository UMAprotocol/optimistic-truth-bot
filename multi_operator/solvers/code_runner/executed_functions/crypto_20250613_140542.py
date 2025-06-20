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
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_eth_price(timestamp):
    """
    Fetches the ETH/USDT price for a specific timestamp using Binance API.
    Args:
        timestamp (int): The timestamp in milliseconds.
    Returns:
        float: The closing price of the ETH/USDT pair.
    """
    params = {
        "symbol": "ETHUSDT",
        "interval": "1h",
        "limit": 1,
        "startTime": timestamp,
        "endTime": timestamp + 3600000  # 1 hour later
    }
    
    try:
        # Try fetching from the proxy endpoint first
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Closing price
    except Exception as e:
        print(f"Proxy failed with error: {e}. Trying primary endpoint.")
        try:
            # Fallback to the primary endpoint if proxy fails
            response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data[0][4])  # Closing price
        except Exception as e:
            print(f"Primary endpoint also failed with error: {e}.")
            return None

def resolve_market():
    """
    Resolves the market based on the price change of ETH/USDT.
    """
    # Define the specific date and time for the market resolution
    target_datetime = datetime(2025, 6, 13, 9, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    target_timestamp = int(target_datetime.timestamp() * 1000)  # Convert to milliseconds

    # Fetch the closing price at the specified time
    closing_price_start = fetch_eth_price(target_timestamp)
    closing_price_end = fetch_eth_price(target_timestamp + 3600000)  # 1 hour later

    if closing_price_start is None or closing_price_end is None:
        print("Failed to fetch required data.")
        return "recommendation: p4"

    # Calculate the percentage change
    percentage_change = ((closing_price_end - closing_price_start) / closing_price_start) * 100

    # Determine the resolution based on the percentage change
    if percentage_change >= 0:
        print(f"ETH price increased or remained the same: {percentage_change}%")
        return "recommendation: p2"  # Up
    else:
        print(f"ETH price decreased: {percentage_change}%")
        return "recommendation: p1"  # Down

if __name__ == "__main__":
    result = resolve_market()
    print(result)