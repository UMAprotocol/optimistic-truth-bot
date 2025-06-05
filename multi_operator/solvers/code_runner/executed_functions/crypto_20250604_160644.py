import requests
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv

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
        # Try fetching data using the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def get_close_price(symbol, target_date_str, target_time_str, timezone_str):
    """
    Get the closing price of a cryptocurrency at a specific time and date.
    """
    # Convert local time to UTC
    tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(f"{target_date_str} {target_time_str}", "%Y-%m-%d %H:%M")
    local_datetime = tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)

    # Convert datetime to milliseconds since epoch
    start_time = int(utc_datetime.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later

    data = fetch_binance_data(symbol, "1m", start_time, end_time)
    if data and len(data) > 0:
        close_price = float(data[0][4])
        return close_price
    else:
        return None

def main():
    # Specific details from the question
    symbol = "BTCUSDT"
    target_date_str = "2025-05-16"
    target_time_str = "12:00"
    timezone_str = "US/Eastern"
    threshold_price = 106000.01

    close_price = get_close_price(symbol, target_date_str, target_time_str, timezone_str)
    if close_price is None:
        print("recommendation: p4")  # Unable to determine due to data fetch failure
    elif close_price >= threshold_price:
        print("recommendation: p2")  # Yes, BTC closed above $106K
    else:
        print("recommendation: p1")  # No, BTC did not close above $106K

if __name__ == "__main__":
    main()