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
        # Try fetching from proxy endpoint
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0][4]  # Close price
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fallback to primary endpoint
        try:
            response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0][4]  # Close price
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
            return None

def resolve_market():
    """
    Resolves the market based on the price change of BTC/USDT on Binance.
    """
    # Define the specific time for the event
    event_time_utc = datetime(2025, 6, 16, 19, 0, 0)  # 3 PM ET in UTC (19:00)
    start_time = int(event_time_utc.timestamp() * 1000)  # Convert to milliseconds
    
    # Fetch the closing price of the 1-hour candle starting at the event time
    close_price = fetch_price_data("BTCUSDT", start_time)
    
    if close_price is None:
        print("recommendation: p3")  # Unknown/50-50 if data is not available
        return
    
    # Compare the close price with the open price to determine the market resolution
    if float(close_price) >= 0:
        print("recommendation: p2")  # Up
    else:
        print("recommendation: p1")  # Down

if __name__ == "__main__":
    resolve_market()