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

def fetch_price(symbol, date_str, timezone_str="US/Eastern"):
    """
    Fetches the closing price of a cryptocurrency from Binance for a specific minute candle.
    
    Args:
        symbol (str): The symbol to fetch, e.g., 'XRPUSDT'
        date_str (str): The date and time in 'YYYY-MM-DD HH:MM' format
        timezone_str (str): The timezone of the given date and time
    
    Returns:
        float: The closing price
    """
    # Convert date_str to UTC timestamp
    local = pytz.timezone(timezone_str)
    naive = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    local_dt = local.localize(naive, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    timestamp = int(utc_dt.timestamp() * 1000)  # Convert to milliseconds

    # Prepare parameters for API request
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": timestamp,
        "endTime": timestamp + 60000  # One minute later
    }

    # Try fetching from the proxy endpoint first
    try:
        response = requests.get(PROXY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])  # Closing price is the fifth element
        return close_price
    except Exception as e:
        print(f"Proxy failed, error: {e}. Trying primary API.")

    # Fallback to the primary API if proxy fails
    try:
        response = requests.get(PRIMARY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])  # Closing price is the fifth element
        return close_price
    except Exception as e:
        print(f"Primary API failed, error: {e}.")
        raise

def main():
    # Define the symbol and times for comparison
    symbol = "XRPUSDT"
    date1 = "2025-06-01 12:00"
    date2 = "2025-06-02 12:00"
    timezone_str = "US/Eastern"

    try:
        # Fetch prices
        price1 = fetch_price(symbol, date1, timezone_str)
        price2 = fetch_price(symbol, date2, timezone_str)

        # Determine the resolution based on prices
        if price1 < price2:
            print("recommendation: p2")  # Up
        elif price1 > price2:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    except Exception as e:
        print(f"Failed to fetch prices or determine resolution, error: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()