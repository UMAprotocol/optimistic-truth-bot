import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from Binance using a proxy endpoint with a fallback to the primary endpoint.
    """
    headers = {'X-MBX-APIKEY': BINANCE_API_KEY}
    params = {
        'symbol': symbol,
        'interval': '1h',
        'startTime': start_time,
        'endTime': end_time,
        'limit': 1
    }

    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
            return None

def resolve_market(symbol, target_date):
    """
    Resolves the market based on the price change of the specified symbol on the target date.
    """
    # Convert date to the beginning and end of the 11AM ET hour in UTC milliseconds
    start_dt = datetime.strptime(f"{target_date} 11:00:00", "%Y-%m-%d %H:%M:%S").timestamp() * 1000
    end_dt = datetime.strptime(f"{target_date} 12:00:00", "%Y-%m-%d %H:%M:%S").timestamp() * 1000

    # Fetch price data
    candle_data = fetch_price_data(symbol, int(start_dt), int(end_dt))
    if candle_data:
        open_price = float(candle_data[1])
        close_price = float(candle_data[4])
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50 due to data fetch failure

def main():
    # Example usage
    result = resolve_market("BTCUSDT", "2025-05-28")
    print(result)

if __name__ == "__main__":
    main()