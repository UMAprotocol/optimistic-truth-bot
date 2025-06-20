import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

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
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
            return None

def get_price_change(symbol, target_datetime):
    """
    Determines the price change for a specific hour candle on Binance.
    """
    # Convert target datetime to the correct format for API request
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds

    # Fetch price data
    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data:
        open_price = float(data[1])
        close_price = float(data[4])
        return ((close_price - open_price) / open_price) * 100
    else:
        return None

def main():
    """
    Main function to determine if the Bitcoin price went up or down.
    """
    target_datetime = datetime(2025, 6, 10, 18, 0, tzinfo=pytz.timezone("US/Eastern"))
    symbol = "BTCUSDT"
    price_change = get_price_change(symbol, target_datetime)

    if price_change is None:
        print("recommendation: p3")  # Unknown or data fetch error
    elif price_change >= 0:
        print("recommendation: p2")  # Price went up
    else:
        print("recommendation: p1")  # Price went down

if __name__ == "__main__":
    main()