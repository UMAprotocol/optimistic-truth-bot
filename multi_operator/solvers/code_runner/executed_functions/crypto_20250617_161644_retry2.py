import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
    }
    headers = {
        "X-MBX-APIKEY": BINANCE_API_KEY
    }

    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the price change of the symbol at the specified target time.
    """
    # Convert target time to milliseconds since this is what Binance API expects
    target_time_ms = int(target_time.timestamp() * 1000)
    # Fetch data for the specific minute
    data = fetch_binance_data(symbol, "1h", target_time_ms, target_time_ms + 60000)

    if data:
        open_price = float(data[1])
        close_price = float(data[4])
        # Determine if the price went up or down
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50

def main():
    # Define the symbol and the specific time for the market resolution
    symbol = "BTCUSDT"
    target_time_str = "2025-06-17 11:00:00"
    timezone_str = "America/New_York"

    # Convert string time to datetime object in the specified timezone
    timezone = pytz.timezone(timezone_str)
    target_time = datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S")
    target_time = timezone.localize(target_time)

    # Resolve the market
    result = resolve_market(symbol, target_time)
    print(result)

if __name__ == "__main__":
    main()