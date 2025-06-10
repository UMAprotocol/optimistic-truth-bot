import requests
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

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
    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def get_close_price(symbol, date_str, timezone_str="US/Eastern"):
    """
    Get the close price for a given symbol at a specific date and time from Binance.
    """
    # Convert date string to the appropriate timestamp
    tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    local_datetime = tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    timestamp = int(utc_datetime.timestamp() * 1000)  # Convert to milliseconds

    # Fetch data from Binance
    data = fetch_binance_data(symbol, "1m", timestamp, timestamp + 60000)  # 1 minute interval
    if data and len(data) > 0:
        close_price = float(data[0][4])  # Close price is the 5th element in the list
        return close_price
    else:
        raise ValueError("No data returned from Binance API.")

def main():
    """
    Main function to determine if Bitcoin price went up or down between two specific dates.
    """
    try:
        # Define the symbol and dates
        symbol = "BTCUSDT"
        date1 = "2025-05-28 12:00"
        date2 = "2025-05-29 12:00"

        # Get close prices for both dates
        close_price1 = get_close_price(symbol, date1)
        close_price2 = get_close_price(symbol, date2)

        # Determine the resolution based on the close prices
        if close_price2 > close_price1:
            print("recommendation: p2")  # Up
        elif close_price2 < close_price1:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    except Exception as e:
        print(f"An error occurred: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()