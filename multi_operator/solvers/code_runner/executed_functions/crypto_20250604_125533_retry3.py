import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_URL = "https://api.binance.com/api/v3"

def get_data(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint.
    """
    try:
        # First try the proxy endpoint
        response = requests.get(f"{PROXY_URL}/klines",
                                params={"symbol": symbol, "interval": "1h", "limit": 1, "startTime": start_time, "endTime": end_time},
                                headers={"X-MBX-APIKEY": BINANCE_API_KEY},
                                timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{PRIMARY_URL}/klines",
                                params={"symbol": symbol, "interval": "1h", "limit": 1, "startTime": start_time, "endTime": end_time},
                                headers={"X-MBX-APIKEY": BINANCE_API_KEY},
                                timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]

def resolve_market(symbol, target_date):
    """
    Resolves the market based on the price change of the symbol on the target date.
    """
    # Convert target date to the beginning of the hour in UTC
    target_datetime = datetime.strptime(target_date, "%Y-%m-%d %H:%M %Z")
    target_datetime_utc = target_datetime.astimezone(pytz.utc)
    start_time = int(target_datetime_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Get data
    candle_data = get_data(symbol, start_time, end_time)
    if candle_data:
        open_price = float(candle_data[1])
        close_price = float(candle_data[4])
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50

def main():
    # Example usage
    result = resolve_market("BTCUSDT", "2025-06-04 05:00 EDT")
    print(result)

if __name__ == "__main__":
    main()