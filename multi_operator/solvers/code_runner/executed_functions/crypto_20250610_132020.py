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
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
            raise

def get_price_change(symbol, target_datetime):
    """
    Calculates the price change for a specific hour candle.
    """
    # Convert target datetime to milliseconds
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds

    # Fetch price data
    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return ((close_price - open_price) / open_price) * 100

def main():
    """
    Main function to determine if the Bitcoin price went up or down.
    """
    target_date_str = "2025-06-10"
    target_hour = 7  # 7 AM ET
    symbol = "BTCUSDT"

    # Convert ET to UTC
    et_timezone = pytz.timezone("US/Eastern")
    utc_timezone = pytz.timezone("UTC")
    target_datetime_et = datetime.strptime(target_date_str, "%Y-%m-%d")
    target_datetime_et = et_timezone.localize(target_datetime_et.replace(hour=target_hour))
    target_datetime_utc = target_datetime_et.astimezone(utc_timezone)

    try:
        price_change = get_price_change(symbol, target_datetime_utc)
        if price_change is not None:
            if price_change >= 0:
                print("recommendation: p2")  # Up
            else:
                print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # Unknown/50-50
    except Exception as e:
        print(f"Error: {e}")
        print("recommendation: p3")  # Unknown/50-50 due to error

if __name__ == "__main__":
    main()