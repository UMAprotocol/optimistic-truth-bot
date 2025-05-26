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

def fetch_price(symbol, date_str, time_str, timezone_str):
    """
    Fetches the closing price of a cryptocurrency from Binance at a specified date and time.
    
    Args:
        symbol (str): The symbol of the cryptocurrency (e.g., 'SOLUSDT').
        date_str (str): The date in 'YYYY-MM-DD' format.
        time_str (str): The time in 'HH:MM' format.
        timezone_str (str): The timezone string (e.g., 'US/Eastern').
    
    Returns:
        float: The closing price.
    """
    # Convert local time to UTC
    local = pytz.timezone(timezone_str)
    naive = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    local_dt = local.localize(naive, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    
    # Convert datetime to milliseconds since epoch
    start_time = int(utc_dt.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later
    
    # First try the proxy endpoint
    try:
        response = requests.get(
            PROXY_API_URL,
            params={
                "symbol": symbol,
                "interval": "1m",
                "limit": 1,
                "startTime": start_time,
                "endTime": end_time
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        print(f"Proxy failed, error: {e}, trying primary API.")
    
    # Fallback to primary API if proxy fails
    try:
        response = requests.get(
            PRIMARY_API_URL,
            params={
                "symbol": symbol,
                "interval": "1m",
                "limit": 1,
                "startTime": start_time,
                "endTime": end_time
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        print(f"Primary API failed, error: {e}")
        raise

def main():
    # Define the symbol and times for the price checks
    symbol = "SOLUSDT"
    date1 = "2025-05-25"
    time1 = "12:00"
    date2 = "2025-05-26"
    time2 = "12:00"
    timezone_str = "US/Eastern"
    
    try:
        # Fetch prices
        price1 = fetch_price(symbol, date1, time1, timezone_str)
        price2 = fetch_price(symbol, date2, time2, timezone_str)
        
        # Determine the resolution
        if price1 < price2:
            print("recommendation: p2")  # Up
        elif price1 > price2:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    except Exception as e:
        print(f"Failed to fetch prices: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()