import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API = "https://api.binance.com/api/v3"
PROXY_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

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
        # Try fetching data from the proxy API first
        response = requests.get(f"{PROXY_API}/klines", params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        print(f"Proxy API failed: {e}, falling back to primary API")
        # Fallback to the primary API if proxy fails
        try:
            response = requests.get(f"{PRIMARY_API}/klines", params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            print(f"Primary API also failed: {e}")
            return None

def resolve_market(symbol, target_date_str, target_hour):
    """
    Resolves the market based on the price change of the specified symbol at the given date and hour.
    """
    # Convert target date and hour to UTC timestamp
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    target_datetime = datetime(target_date.year, target_date.month, target_date.day, target_hour, 0, 0)
    start_time = int(target_datetime.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later

    # Fetch price data
    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data:
        open_price = float(data[1])
        close_price = float(data[4])
        price_change_percentage = ((close_price - open_price) / open_price) * 100

        # Determine resolution based on price change
        if price_change_percentage >= 0:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50 due to data fetch failure

def main():
    # Example usage
    symbol = "ETHUSDT"
    target_date_str = "2025-06-14"
    target_hour = 21  # 9 PM ET, assuming the server is in ET
    result = resolve_market(symbol, target_date_str, target_hour)
    print(result)

if __name__ == "__main__":
    main()