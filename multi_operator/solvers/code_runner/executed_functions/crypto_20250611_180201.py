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
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")

    try:
        # Fallback to the primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Primary endpoint also failed: {e}")
        return None

def get_price_change(symbol, target_datetime):
    """
    Calculates the price change for a specific hour candle.
    """
    # Convert target datetime to the correct format for the API call
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = int((target_datetime + timedelta(minutes=59)).timestamp() * 1000)

    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return ((close_price - open_price) / open_price) * 100
    else:
        return None

def main():
    """
    Main function to determine if the Bitcoin price went up or down.
    """
    target_datetime = datetime(2025, 6, 11, 13, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
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