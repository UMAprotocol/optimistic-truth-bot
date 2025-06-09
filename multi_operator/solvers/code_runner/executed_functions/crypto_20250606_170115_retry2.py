import requests
import os
from datetime import datetime
from pytz import timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint.
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
        # Try proxy endpoint first
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]

def get_price_change(symbol, start_time, end_time):
    """
    Calculates the price change percentage between two times for a given symbol.
    """
    data_start = fetch_binance_data(symbol, "1h", start_time, end_time)
    data_end = fetch_binance_data(symbol, "1h", end_time, end_time + 3600000)  # 1 hour later

    if data_start and data_end:
        open_price = float(data_start[1])
        close_price = float(data_end[4])
        change_percent = ((close_price - open_price) / open_price) * 100
        return change_percent
    return None

def main():
    """
    Main function to determine if the Bitcoin price went up or down.
    """
    symbol = "BTCUSDT"
    et_timezone = timezone('US/Eastern')
    target_date = datetime(2025, 6, 6, 12, 0, 0, tzinfo=et_timezone)
    start_time = int(target_date.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time

    try:
        price_change = get_price_change(symbol, start_time, end_time)
        if price_change is not None:
            if price_change >= 0:
                print("recommendation: p2")  # Up
            else:
                print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # Unknown/50-50
    except Exception as e:
        print(f"Error occurred: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()