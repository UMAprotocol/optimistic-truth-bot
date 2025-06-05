import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Define the API endpoints
PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_URL = "https://api.binance.com/api/v3"

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from the Binance API using a proxy and falls back to the primary endpoint if necessary.
    
    Args:
        symbol (str): The symbol to fetch data for.
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    
    Returns:
        float: The highest price from the fetched data.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Max limit to ensure coverage of the period
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data using the proxy URL
        response = requests.get(PROXY_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            # Extract the highest price from the 'High' value in each candle
            high_prices = [float(candle[2]) for candle in data]
            return max(high_prices)
    except Exception as e:
        print(f"Proxy failed with error: {e}, falling back to primary endpoint.")
        # Fallback to the primary endpoint
        try:
            response = requests.get(f"{PRIMARY_URL}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                high_prices = [float(candle[2]) for candle in data]
                return max(high_prices)
        except Exception as e:
            print(f"Primary endpoint also failed with error: {e}")
            return None

def main():
    # Define the symbol and the time period for the query
    symbol = "FARTCOINSOL"
    start_date = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone("US/Eastern"))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone("US/Eastern"))
    
    # Convert datetime to milliseconds since epoch
    start_time_ms = int(start_date.timestamp() * 1000)
    end_time_ms = int(end_date.timestamp() * 1000)
    
    # Fetch the highest price in the given period
    highest_price = fetch_price_data(symbol, start_time_ms, end_time_ms)
    
    # Determine the resolution based on the highest price
    if highest_price is not None:
        if highest_price >= 2.50:
            print("recommendation: p2")  # Yes, it reached $2.50 or higher
        else:
            print("recommendation: p1")  # No, it did not reach $2.50
    else:
        print("recommendation: p3")  # Unknown or data fetch error

if __name__ == "__main__":
    main()