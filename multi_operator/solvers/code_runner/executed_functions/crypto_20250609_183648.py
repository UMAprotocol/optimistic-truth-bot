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
    Implements a fallback mechanism from proxy to primary API endpoint.
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
    Checks if the price of a cryptocurrency dipped to or below a threshold between two dates.
    """
    # Convert dates to timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d %H:%M"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d %H:%M"))

    start_timestamp = int(start_dt.timestamp() * 1000)
    end_timestamp = int(end_dt.timestamp() * 1000)

    # Fetch price data in chunks (due to API limit constraints)
    current_start = start_timestamp
    while current_start < end_timestamp:
        current_end = min(current_start + 86400000, end_timestamp)  # 1 day in milliseconds
        data = fetch_price_data(symbol, current_start, current_end)
        if data:
            for candle in data:
                low_price = float(candle[3])  # Low price is the fourth element in the list
                if low_price <= threshold_price:
                    return True
        current_start += 86400000 + 1  # Move to the next day

    return False

def main():
    symbol = "SUIUSDT"
    start_date = "2025-05-07 00:00"
    end_date = "2025-05-31 23:59"
    threshold_price = 2.4

    if check_price_dip_to_threshold(symbol, start_date, end_date, threshold_price):
        print("recommendation: p2")  # Yes, price dipped to $2.4 or lower
    else:
        print("recommendation: p1")  # No, price did not dip to $2.4 or lower

if __name__ == "__main__":
    main()