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
        # Try fetching data from the proxy endpoint
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

def get_candle_data(symbol, target_datetime):
    """
    Get the closing price of the 1-hour candle for the given datetime.
    """
    # Convert datetime to milliseconds
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        # Extract the closing price from the first candle data
        close_price = float(data[0][4])
        return close_price
    else:
        return None

def main():
    # Define the target date and time
    target_datetime_str = "2025-06-11 16:00:00"
    target_timezone = pytz.timezone("US/Eastern")
    target_datetime = datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S")
    target_datetime = target_timezone.localize(target_datetime)

    # Convert target datetime to UTC
    target_datetime_utc = target_datetime.astimezone(pytz.utc)

    # Get the closing price of the 1-hour candle starting at the target datetime
    symbol = "BTCUSDT"
    close_price_start = get_candle_data(symbol, target_datetime_utc)

    # Get the closing price of the 1-hour candle one hour later
    close_price_end = get_candle_data(symbol, target_datetime_utc + timedelta(hours=1))

    if close_price_start is not None and close_price_end is not None:
        # Determine if the price went up or down
        if close_price_end >= close_price_start:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 due to data fetch failure

if __name__ == "__main__":
    main()