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
        # Try fetching data using the proxy URL first
        response = requests.get(PROXY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy failed with error: {e}, trying primary API endpoint.")
        # Fallback to the primary API endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
            return None

def get_close_price(symbol, date_str, timezone_str="US/Eastern"):
    """
    Get the closing price of a symbol at a specific date and time from Binance.
    """
    # Convert date string to the correct timestamp
    tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    local_datetime = tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)

    # Convert datetime to milliseconds since epoch
    start_time = int(utc_datetime.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later

    data = fetch_binance_data(symbol, "1m", start_time, end_time)
    if data and len(data) > 0:
        close_price = float(data[0][4])  # Close price is the 5th element in the list
        return close_price
    else:
        return None

def main():
    """
    Main function to determine if BTC closed below $100K on May 16, 2025 at 12:00 ET.
    """
    close_price = get_close_price("BTCUSDT", "2025-05-16 12:00", "US/Eastern")
    if close_price is not None:
        if close_price <= 99999.99:
            print("recommendation: p2")  # Yes, it closed below $100K
        else:
            print("recommendation: p1")  # No, it did not close below $100K
    else:
        print("recommendation: p3")  # Unknown or data not available

if __name__ == "__main__":
    main()