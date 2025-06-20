import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

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
    headers = {
        "X-MBX-APIKEY": BINANCE_API_KEY
    }

    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        print(f"Proxy failed with error: {e}, falling back to primary API.")
        try:
            # Fallback to the primary API endpoint
            response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
            return None

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price change of the cryptocurrency.
    """
    # Convert target datetime to UTC milliseconds
    target_time_utc = int(target_datetime.timestamp() * 1000)
    # Fetch price data for the 1 hour interval starting at target time
    data = fetch_price_data(symbol, "1h", target_time_utc, target_time_utc + 3600000)
    
    if data:
        open_price = float(data[1])
        close_price = float(data[4])
        price_change = close_price - open_price
        if price_change >= 0:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 due to data fetch failure

def main():
    # Define the symbol and target datetime
    symbol = "ETHUSDT"
    target_datetime = datetime(2025, 6, 12, 3, 0, tzinfo=pytz.timezone("US/Eastern"))
    
    # Resolve the market based on the price change
    result = resolve_market(symbol, target_datetime)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()