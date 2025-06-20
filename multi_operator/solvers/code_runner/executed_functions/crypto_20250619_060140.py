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
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, interval, start_time, end_time):
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
        # Try fetching data using the proxy endpoint
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def get_eth_price_data(date_str, hour):
    """
    Get the open and close price of ETH/USDT for a specific hour on a given date.
    """
    # Convert date and hour to the correct timestamp
    dt = datetime.strptime(date_str + f" {hour}:00:00", "%Y-%m-%d %H:%M:%S")
    dt = pytz.timezone("America/New_York").localize(dt)
    dt_utc = dt.astimezone(pytz.utc)
    
    start_time = int(dt_utc.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # Add one hour in milliseconds
    
    # Fetch data from Binance
    data = fetch_binance_data("ETHUSDT", "1h", start_time, end_time)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    else:
        raise ValueError("No data returned from API.")

def resolve_market():
    """
    Resolve the market based on the open and close prices of ETH/USDT.
    """
    try:
        open_price, close_price = get_eth_price_data("2025-06-19", 1)  # Date and hour as specified
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    except Exception as e:
        print(f"Error fetching or processing data: {e}")
        return "recommendation: p3"  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    result = resolve_market()
    print(result)