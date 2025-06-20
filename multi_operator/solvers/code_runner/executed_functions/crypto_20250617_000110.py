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

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance using the proxy endpoint with a fallback to the primary endpoint.
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
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
            raise

def analyze_price_change(data):
    """
    Analyzes the price change from the fetched data.
    """
    if not data or len(data) < 1 or len(data[0]) < 5:
        return "p4"  # Unable to resolve due to insufficient data

    open_price = float(data[0][1])
    close_price = float(data[0][4])

    if close_price >= open_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    """
    Main function to execute the price analysis for Ethereum on a specific date and time.
    """
    symbol = "ETHUSDT"
    interval = "1h"
    # Specific date and time for the analysis
    target_datetime = datetime(2025, 6, 16, 19, 0)  # June 16, 7 PM ET
    # Convert to milliseconds since this is what Binance API expects
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    try:
        data = fetch_price_data(symbol, interval, start_time, end_time)
        result = analyze_price_change(data)
        print(f"recommendation: {result}")
    except Exception as e:
        print(f"Failed to fetch or analyze data: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()