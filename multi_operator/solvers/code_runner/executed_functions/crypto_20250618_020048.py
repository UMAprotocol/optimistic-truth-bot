import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_PRIMARY_URL = "https://api.binance.com/api/v3"
BINANCE_PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary request fails.
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
        response = requests.get(f"{BINANCE_PROXY_URL}/klines", params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        print(f"Proxy failed with error: {e}, trying primary endpoint.")
        # Fallback to the primary endpoint if proxy fails
        try:
            response = requests.get(f"{BINANCE_PRIMARY_URL}/klines", params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            print(f"Primary endpoint also failed with error: {e}")
            return None

def resolve_market(symbol, target_date):
    """
    Resolves the market based on the price change of the symbol on the target date.
    """
    # Convert target date to the start and end timestamps for the 1-hour candle
    start_dt = datetime.strptime(target_date, "%Y-%m-%d %H:%M:%S")
    start_timestamp = int(start_dt.timestamp() * 1000)  # Convert to milliseconds
    end_timestamp = start_timestamp + 3600000  # Add one hour in milliseconds

    # Fetch the candle data
    candle_data = fetch_binance_data(symbol, "1h", start_timestamp, end_timestamp)
    if candle_data:
        open_price = float(candle_data[1])
        close_price = float(candle_data[4])
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50 if data is not available

def main():
    # Example usage
    symbol = "BTCUSDT"
    target_date = "2025-06-17 21:00:00"  # June 17, 9 PM ET
    result = resolve_market(symbol, target_date)
    print(result)

if __name__ == "__main__":
    main()