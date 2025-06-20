import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_btc_data(start_time, end_time):
    """
    Fetches BTC data from Binance API between specified start and end times.
    Uses a proxy endpoint with a fallback to the primary endpoint.
    """
    params = {
        "symbol": "BTCUSDT",
        "interval": "1d",
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Proxy failed, error: {e}. Falling back to primary endpoint.")
        # Fallback to the primary endpoint
        response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params)
        response.raise_for_status()
        data = response.json()
        return data

def calculate_btc_purchases(data):
    """
    Calculate the total amount of BTC purchased based on the closing prices and volumes.
    """
    total_btc = sum(float(day[5]) for day in data)  # Volume is at index 5
    return total_btc

def main():
    # Define the period of interest
    start_date = datetime(2025, 6, 10)
    end_date = datetime(2025, 6, 16)
    start_time = int(start_date.timestamp() * 1000)  # Convert to milliseconds
    end_time = int((end_date.timestamp() + 86400) * 1000)  # Include the end day fully

    # Fetch BTC data
    btc_data = fetch_btc_data(start_time, end_time)

    # Calculate total BTC purchases
    total_btc_purchased = calculate_btc_purchases(btc_data)

    # Determine the resolution based on the total BTC purchased
    if total_btc_purchased >= 8001:
        print("recommendation: p2")  # Yes, more than 8001 BTC purchased
    else:
        print("recommendation: p1")  # No, less than 8001 BTC purchased

if __name__ == "__main__":
    main()