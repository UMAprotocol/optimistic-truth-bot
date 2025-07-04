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

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
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
        # Try fetching data using the proxy API first
        response = requests.get(PROXY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy API failed, error: {e}. Trying primary API.")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary API also failed, error: {e}.")
            return None

def get_price_change(symbol, target_date_str, target_hour):
    """
    Determines the price change for a specific hour candle on Binance.
    """
    # Convert target date and hour to the correct timestamp
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    target_date = target_date.replace(hour=target_hour, tzinfo=pytz.timezone("US/Eastern"))
    target_date_utc = target_date.astimezone(pytz.utc)

    start_time = int(target_date_utc.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later

    # Fetch data from Binance
    data = fetch_binance_data(symbol, "1h", start_time, end_time)
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change = (close_price - open_price) / open_price * 100
        return price_change
    else:
        return None

def main():
    """
    Main function to determine if the Bitcoin price went up or down.
    """
    symbol = "BTCUSDT"
    target_date_str = "2025-06-06"
    target_hour = 23  # 11 PM ET

    price_change = get_price_change(symbol, target_date_str, target_hour)
    if price_change is not None:
        if price_change >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 due to data fetch failure

if __name__ == "__main__":
    main()