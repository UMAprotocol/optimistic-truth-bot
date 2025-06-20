import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_URL = "https://api.binance.com/api/v3"

def fetch_price_data(symbol, start_time):
    """
    Fetches price data from Binance using a proxy and falls back to the primary endpoint if necessary.
    """
    params = {
        "symbol": symbol,
        "interval": "1h",
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later in milliseconds
    }
    
    try:
        # Try fetching data using the proxy endpoint
        response = requests.get(f"{PROXY_URL}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0][4]  # Close price of the candle
    except Exception as e:
        print(f"Proxy failed with error: {e}, trying primary endpoint.")
        # Fallback to the primary endpoint
        try:
            response = requests.get(f"{PRIMARY_URL}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0][4]  # Close price of the candle
        except Exception as e:
            print(f"Primary endpoint also failed with error: {e}")
            return None

def resolve_market():
    """
    Resolves the market based on the price change of BTC/USDT on Binance.
    """
    # Define the specific time for the event
    event_time_utc = datetime(2025, 6, 15, 10)  # 6 AM ET in UTC (10 AM UTC)
    start_time = int(event_time_utc.timestamp() * 1000)  # Convert to milliseconds
    
    # Fetch the closing price of the 1-hour candle starting at the event time
    close_price_start = fetch_price_data("BTCUSDT", start_time)
    if close_price_start is None:
        return "recommendation: p4"  # Unable to fetch data
    
    # Fetch the closing price of the previous 1-hour candle
    close_price_previous = fetch_price_data("BTCUSDT", start_time - 3600000)
    if close_price_previous is None:
        return "recommendation: p4"  # Unable to fetch data
    
    # Calculate the percentage change
    try:
        close_price_start = float(close_price_start)
        close_price_previous = float(close_price_previous)
        percentage_change = ((close_price_start - close_price_previous) / close_price_previous) * 100
    except (ValueError, TypeError):
        return "recommendation: p4"  # Error in data conversion
    
    # Determine the resolution based on the percentage change
    if percentage_change >= 0:
        return "recommendation: p2"  # Market resolves to "Up"
    else:
        return "recommendation: p1"  # Market resolves to "Down"

if __name__ == "__main__":
    result = resolve_market()
    print(result)