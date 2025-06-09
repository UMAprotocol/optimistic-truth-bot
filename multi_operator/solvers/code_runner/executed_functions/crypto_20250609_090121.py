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

def fetch_price_data(symbol, start_time):
    """
    Fetches price data for a given symbol at a specified start time using Binance API.
    Implements a fallback mechanism from proxy to primary endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": "1h",
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later in milliseconds
    }
    
    try:
        # Try fetching from proxy endpoint first
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0][4]  # Close price of the candle
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fallback to primary endpoint
        try:
            response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0][4]  # Close price of the candle
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
            return None

def resolve_market():
    """
    Resolves the market based on the price change of BTC/USDT on Binance.
    """
    # Define the specific time for the market resolution
    target_date = datetime(2025, 6, 9, 4, 0)  # June 9, 2025, 4 AM ET
    # Convert to UTC and then to milliseconds since this is what Binance API expects
    target_date_utc = target_date - timedelta(hours=4)  # Assuming ET is UTC-4
    start_time_ms = int(target_date_utc.timestamp() * 1000)
    
    # Fetch the closing price at the specified time
    close_price_start = fetch_price_data("BTCUSDT", start_time_ms)
    if close_price_start is None:
        return "recommendation: p3"  # Unknown or API failure
    
    # Fetch the closing price one hour later
    close_price_end = fetch_price_data("BTCUSDT", start_time_ms + 3600000)
    if close_price_end is None:
        return "recommendation: p3"  # Unknown or API failure
    
    # Determine if the price went up or down
    if float(close_price_end) >= float(close_price_start):
        return "recommendation: p2"  # Up
    else:
        return "recommendation: p1"  # Down

if __name__ == "__main__":
    result = resolve_market()
    print(result)