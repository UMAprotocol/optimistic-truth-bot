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
PRIMARY_API_URL = "https://api.binance.com/api/v3"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
    
    Args:
        symbol (str): The symbol to fetch data for.
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    
    Returns:
        float: The lowest price within the given time frame.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Max limit
        "startTime": start_time,
        "endTime": end_time
    }

    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(f"{PROXY_API_URL}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Proxy failed, trying primary API: {e}")
        # Fallback to the primary API endpoint
        try:
            response = requests.get(f"{PRIMARY_API_URL}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Both proxy and primary API requests failed: {e}")
            return None

    # Find the lowest price in the returned data
    lowest_price = float('inf')
    for candle in data:
        low_price = float(candle[3])  # Low price is at index 3
        if low_price < lowest_price:
            lowest_price = low_price

    return lowest_price

def check_price_dip(symbol, start_date, end_date, target_price):
    """
    Checks if the price of a cryptocurrency dipped to or below a target price between two dates.
    
    Args:
        symbol (str): The cryptocurrency symbol.
        start_date (str): Start date in YYYY-MM-DD format.
        end_date (str): End date in YYYY-MM-DD format.
        target_price (float): Target price to check.
    
    Returns:
        str: 'p1' if the price never dipped to or below the target price, 'p2' if it did.
    """
    # Convert dates to UTC timestamps
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # Include the end day fully
    start_ts = int(start_dt.replace(tzinfo=pytz.UTC).timestamp() * 1000)
    end_ts = int(end_dt.replace(tzinfo=pytz.UTC).timestamp() * 1000)

    # Fetch the lowest price in the given time frame
    lowest_price = fetch_price_data(symbol, start_ts, end_ts)

    if lowest_price is None:
        return "p4"  # Unable to determine due to API failure

    # Determine if the price dipped to or below the target price
    if lowest_price <= target_price:
        return "p2"  # Yes, it dipped
    else:
        return "p1"  # No, it did not dip

def main():
    # Example usage
    symbol = "HOUSE/SOL"
    start_date = "2025-05-07"
    end_date = "2025-05-31"
    target_price = 0.018
    result = check_price_dip(symbol, start_date, end_date, target_price)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()