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
    Fetches price data from Binance API for a given symbol within the specified time range.
    Implements a fallback mechanism from proxy to primary API endpoint.
    
    Args:
        symbol (str): The symbol to fetch data for, e.g., 'XRPUSDT'.
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    
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

def check_xrp_dip_to_one_dollar(start_date, end_date):
    """
    Checks if XRP dipped to $1.00 or lower between the given start and end dates.
    
    Args:
        start_date (str): Start date in 'YYYY-MM-DD' format.
        end_date (str): End date in 'YYYY-MM-DD' format.
    
    Returns:
        str: 'p1' if no dip to $1.00 or lower, 'p2' if there was a dip, 'p4' if data is inconclusive.
    """
    # Convert dates to UTC timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))
    
    start_ts = int(start_dt.timestamp() * 1000)
    end_ts = int(end_dt.timestamp() * 1000)
    
    # Fetch price data
    data = fetch_price_data("XRPUSDT", start_ts, end_ts)
    
    if data:
        # Check if any low price in the data is $1.00 or lower
        for candle in data:
            low_price = float(candle[3])
            if low_price <= 1.00:
                return "p2"  # Yes, there was a dip to $1.00 or lower
        return "p1"  # No dip to $1.00 or lower
    else:
        return "p4"  # Inconclusive due to data fetch failure

def main():
    # Define the date range for May 2025
    start_date = "2025-05-01"
    end_date = "2025-05-31"
    
    # Check if XRP dipped to $1.00 or lower in May 2025
    result = check_xrp_dip_to_one_dollar(start_date, end_date)
    
    # Print the result
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()