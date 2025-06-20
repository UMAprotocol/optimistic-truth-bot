import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"

def fetch_price_data(symbol, start_time):
    """
    Fetches price data from Binance using a proxy endpoint with a fallback to the primary endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": "1h",
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later
    }
    
    try:
        # Try proxy endpoint first
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]  # Return the first (and only) candle
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]  # Return the first (and only) candle
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
            return None

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price data fetched for the specified datetime.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    
    # Fetch price data
    candle = fetch_price_data(symbol, start_time)
    
    if candle:
        open_price = float(candle[1])
        close_price = float(candle[4])
        
        # Determine resolution based on open and close prices
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50 if no data available

def main():
    # Example: Solana on June 18, 2025, 12 AM ET
    symbol = "SOLUSDT"
    target_datetime_str = "2025-06-18 00:00:00"
    timezone_str = "US/Eastern"
    
    # Convert string to datetime
    tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S")
    target_datetime = tz.localize(naive_datetime)
    
    # Convert to UTC
    target_datetime_utc = target_datetime.astimezone(pytz.utc)
    
    # Resolve the market
    result = resolve_market(symbol, target_datetime_utc)
    print(result)

if __name__ == "__main__":
    main()