import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_data_from_binance(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market(symbol, target_date_time):
    """
    Resolves the market based on the opening and closing prices of the specified symbol at the given date and time.
    """
    # Convert target datetime to UTC timestamp in milliseconds
    target_utc = int(target_date_time.replace(tzinfo=pytz.utc).timestamp() * 1000)
    
    # Fetch the 1-hour candle data for the specified time
    data = fetch_data_from_binance(symbol, "1h", target_utc, target_utc + 3600000)  # 1 hour in milliseconds
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 if no data available

def main():
    # Example: Ethereum price on June 18, 2025, 9 AM ET
    symbol = "ETHUSDT"
    target_date_str = "2025-06-18"
    target_time_str = "09:00:00"
    timezone_str = "US/Eastern"
    
    # Parse the target datetime in the specified timezone
    tz = pytz.timezone(timezone_str)
    target_date_time = datetime.strptime(f"{target_date_str} {target_time_str}", "%Y-%m-%d %H:%M:%S")
    target_date_time = tz.localize(target_date_time).astimezone(pytz.utc)
    
    # Resolve the market
    result = resolve_market(symbol, target_date_time)
    
    # Print the result
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()