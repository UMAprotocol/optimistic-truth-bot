import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API keys
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
        if data:
            return data
    except Exception as e:
        print(f"Proxy failed with error: {e}, falling back to primary API.")
        # Fallback to the primary API endpoint
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
            return None

def get_eth_price_change():
    """
    Determines if the ETH price went up or down at the specified time.
    """
    # Define the time for the 1H candle on June 17, 12 PM ET
    target_time = datetime(2025, 6, 17, 12, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    start_time = int(target_time.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later

    # Fetch the price data for ETH/USDT
    data = fetch_price_data("ETHUSDT", "1h", start_time, end_time)
    
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 due to data fetch failure

def main():
    result = get_eth_price_change()
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()