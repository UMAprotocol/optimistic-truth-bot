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
    Fetches price data from Binance API with a fallback to a proxy endpoint.
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
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
            return None

def get_eth_price_change():
    """
    Determines the price change of ETH/USDT for the specific 1-hour candle on June 12, 2025, 3 PM ET.
    """
    # Define the specific date and time
    target_datetime = datetime(2025, 6, 12, 15, 0, 0)  # June 12, 2025, 3 PM ET
    et_timezone = pytz.timezone('US/Eastern')
    target_datetime = et_timezone.localize(target_datetime)

    # Convert to UTC
    target_datetime_utc = target_datetime.astimezone(pytz.utc)

    # Calculate start and end times in milliseconds for the API
    start_time = int(target_datetime_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch price data for ETH/USDT
    data = fetch_price_data("ETHUSDT", "1h", start_time, end_time)

    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change_percentage = ((close_price - open_price) / open_price) * 100

        # Determine resolution based on price change
        if price_change_percentage >= 0:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 due to data fetch failure

def main():
    resolution = get_eth_price_change()
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()