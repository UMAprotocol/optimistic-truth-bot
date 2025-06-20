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
    Fetches price data from Binance API with a fallback to a proxy server.
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
        return data
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price data of the specified symbol at the target datetime.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later

    # Fetch price data
    data = fetch_price_data(symbol, "1h", start_time, end_time)
    
    if not data or len(data) == 0:
        return "recommendation: p3"  # Unknown or no data available

    open_price = float(data[0][1])
    close_price = float(data[0][4])

    # Determine market resolution
    if close_price >= open_price:
        return "recommendation: p2"  # Up
    else:
        return "recommendation: p1"  # Down

def main():
    # Example: Solana price on June 18, 2025, 7 PM ET
    symbol = "SOLUSDT"
    target_datetime_str = "2025-06-18 19:00:00"
    timezone_str = "US/Eastern"

    # Convert string to datetime
    target_datetime = datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S")
    target_datetime = pytz.timezone(timezone_str).localize(target_datetime)
    target_datetime = target_datetime.astimezone(pytz.utc)

    # Resolve the market
    result = resolve_market(symbol, target_datetime)
    print(result)

if __name__ == "__main__":
    main()