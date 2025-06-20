import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
    """
    params = {
        "symbol": symbol,
        "interval": "1h",
        "startTime": start_time,
        "endTime": end_time
    }
    headers = {
        "X-MBX-APIKEY": BINANCE_API_KEY
    }

    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market(symbol, target_date):
    """
    Resolves the market based on the price movement of the specified symbol on the target date.
    """
    # Convert target date to UTC timestamp at 6 PM ET
    target_datetime = datetime.strptime(target_date + " 18:00:00", "%Y-%m-%d %H:%M:%S")
    et_timezone = pytz.timezone("US/Eastern")
    target_datetime = et_timezone.localize(target_datetime)
    target_utc_datetime = target_datetime.astimezone(pytz.utc)

    # Calculate start and end timestamps in milliseconds
    start_time = int(target_utc_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch price data
    data = fetch_price_data(symbol, start_time, end_time)
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])

        # Determine market resolution
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50 if no data

def main():
    # Example usage
    symbol = "SOLUSDT"
    target_date = "2025-06-18"
    result = resolve_market(symbol, target_date)
    print(result)

if __name__ == "__main__":
    main()