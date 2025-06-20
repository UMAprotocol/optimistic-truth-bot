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
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fallback to the primary endpoint
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market(symbol, target_date_str, target_hour):
    """
    Resolves the market based on the opening and closing prices of the specified symbol at the given date and hour.
    """
    # Convert target date and hour to UTC timestamp
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    target_date = pytz.timezone("US/Eastern").localize(target_date.replace(hour=target_hour))
    target_date_utc = target_date.astimezone(pytz.utc)
    
    start_time = int(target_date_utc.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later in milliseconds
    
    # Fetch price data
    data = fetch_price_data(symbol, "1h", start_time, end_time)
    
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 if no data available

def main():
    """
    Main function to handle the resolution of the market.
    """
    symbol = "ETHUSDT"
    target_date_str = "2025-06-18"
    target_hour = 15  # 3 PM ET
    
    resolution = resolve_market(symbol, target_date_str, target_hour)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()