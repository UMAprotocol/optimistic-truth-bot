import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

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
    
    Args:
        symbol (str): The symbol to fetch data for, e.g., 'SUIUSDT'.
        start_time (int): Start time in milliseconds since the epoch.
        end_time (int): End time in milliseconds since the epoch.
    
    Returns:
        list: List of price data or None if both requests fail.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Maximum limit
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

    try:
        # Fallback to the primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Primary endpoint also failed: {str(e)}")
        return None

def check_price_dip_to_threshold(symbol, start_date, end_date, threshold):
    """
    Checks if the price of a symbol dipped to or below a threshold between two dates.
    
    Args:
        symbol (str): The trading symbol, e.g., 'SUIUSDT'.
        start_date (str): Start date in 'YYYY-MM-DD' format.
        end_date (str): End date in 'YYYY-MM-DD' format.
        threshold (float): Price threshold to check.
    
    Returns:
        str: 'p1' if no dip, 'p2' if dipped, 'p4' if data unavailable.
    """
    # Convert dates to UTC timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))

    start_ts = int(start_dt.timestamp() * 1000)
    end_ts = int(end_dt.timestamp() * 1000)

    # Fetch price data
    price_data = fetch_price_data(symbol, start_ts, end_ts)

    if price_data:
        # Check if any low price in the data dips to or below the threshold
        for candle in price_data:
            low_price = float(candle[3])  # Low price is the fourth element in the list
            if low_price <= threshold:
                return "p2"  # Yes, price dipped to or below threshold
        return "p1"  # No, price did not dip to or below threshold
    else:
        return "p4"  # Data unavailable

def main():
    # Define the parameters for the check
    symbol = "SUIUSDT"
    start_date = "2025-05-07"
    end_date = "2025-05-31"
    threshold = 2.2

    # Perform the check
    result = check_price_dip_to_threshold(symbol, start_date, end_date, threshold)
    
    # Print the result
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()