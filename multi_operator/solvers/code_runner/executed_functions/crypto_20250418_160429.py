import requests
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def get_binance_data(symbol, start_time, end_time):
    """
    Fetches the close price of a cryptocurrency from Binance using the proxy endpoint with a fallback to the primary endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price

def resolve_market():
    """
    Resolves the market based on the close price of XRPUSDT on Binance at a specific time.
    """
    # Define the specific date and time for the market resolution
    target_date = "2025-04-18"
    target_hour = 12  # Noon
    target_minute = 0
    timezone_str = "US/Eastern"
    symbol = "XRPUSDT"
    
    # Convert the target time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    target_time_local = tz.localize(datetime.strptime(f"{target_date} {target_hour:02d}:{target_minute:02d}:00", "%Y-%m-%d %H:%M:%S"))
    target_time_utc = target_time_local.astimezone(timezone.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)
    end_time_ms = start_time_ms + 60000  # 1 minute later in milliseconds

    # Fetch the close price from Binance
    close_price = get_binance_data(symbol, start_time_ms, end_time_ms)
    
    # Determine the resolution based on the close price
    if close_price >= 2.00001:
        print("recommendation: p2")  # Yes
    else:
        print("recommendation: p1")  # No

if __name__ == "__main__":
    resolve_market()