import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from Binance API for a given symbol within a specified time range.
    Implements a fallback from proxy to primary API endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Maximum allowed by Binance for one request
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
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def check_price_dip_to_threshold(symbol, start_date, end_date, threshold_price):
    """
    Checks if the price of a given symbol dipped to or below a threshold price between start_date and end_date.
    """
    # Convert dates to milliseconds since the epoch
    start_dt = datetime.strptime(start_date, "%Y-%m-%d %H:%M")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d %H:%M")
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(start_dt).astimezone(pytz.utc)
    end_dt = tz.localize(end_dt).astimezone(pytz.utc)

    start_time = int(start_dt.timestamp() * 1000)
    end_time = int(end_dt.timestamp() * 1000)

    # Fetch price data in chunks (due to API limit constraints)
    while start_time < end_time:
        temp_end_time = min(start_time + 86400000, end_time)  # 1 day's worth of milliseconds
        data = fetch_price_data(symbol, start_time, temp_end_time)
        if data:
            for item in data:
                low_price = float(item[3])  # Low price is the fourth item in the list
                if low_price <= threshold_price:
                    return True
        start_time += 86400000 + 1  # Move to the next day

    return False

def main():
    symbol = "SUIUSDT"
    start_date = "2025-05-07 00:00"
    end_date = "2025-05-31 23:59"
    threshold_price = 2.6

    if check_price_dip_to_threshold(symbol, start_date, end_date, threshold_price):
        print("recommendation: p2")  # Yes, price dipped to $2.6 or lower
    else:
        print("recommendation: p1")  # No, price did not dip to $2.6 or lower

if __name__ == "__main__":
    main()