import requests
import os
from datetime import datetime
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
    Fetches price data from Binance using a proxy and falls back to the primary endpoint if necessary.
    """
    params = {
        "symbol": symbol,
        "interval": "1h",
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later
    }
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]  # Return the first (and only) candle
    except Exception as e:
        print(f"Proxy failed, error: {e}, trying primary endpoint.")
        # Fallback to the primary endpoint
        try:
            response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]  # Return the first (and only) candle
        except Exception as e:
            print(f"Primary endpoint also failed, error: {e}")
            return None

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price data of the specified symbol at the target datetime.
    """
    # Convert datetime to milliseconds since epoch
    target_timestamp = int(target_datetime.timestamp() * 1000)
    
    # Fetch price data
    candle = fetch_price_data(symbol, target_timestamp)
    
    if candle:
        open_price = float(candle[1])
        close_price = float(candle[4])
        
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50 if no data

def main():
    # Example usage
    symbol = "ETHUSDT"
    target_datetime_str = "2025-06-19 21:00:00"
    timezone_str = "America/New_York"
    
    # Convert string to datetime object in the specified timezone
    timezone = pytz.timezone(timezone_str)
    target_datetime = datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S")
    target_datetime = timezone.localize(target_datetime)
    
    # Resolve the market
    result = resolve_market(symbol, target_datetime)
    print(result)

if __name__ == "__main__":
    main()