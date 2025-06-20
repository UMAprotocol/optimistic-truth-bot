import requests
import os
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy endpoint.
    
    Args:
        symbol (str): The symbol to fetch data for.
        interval (str): The interval for the klines data.
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    
    Returns:
        dict: The JSON response containing the price data.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market(symbol, target_date_str, target_hour):
    """
    Resolves the market based on the price data of the specified symbol at the given date and hour.
    
    Args:
        symbol (str): The cryptocurrency symbol.
        target_date_str (str): The target date in 'YYYY-MM-DD' format.
        target_hour (int): The hour of the day in 24-hour format.
    
    Returns:
        str: The resolution of the market ('p1', 'p2', or 'p3').
    """
    # Convert the target time to UTC timestamp
    tz = pytz.timezone("US/Eastern")
    target_datetime = datetime.strptime(target_date_str, "%Y-%m-%d")
    target_datetime = target_datetime.replace(hour=target_hour, tzinfo=tz)
    target_time_utc = target_datetime.astimezone(timezone.utc)
    
    start_time_ms = int(target_time_utc.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later
    
    # Fetch price data
    data = fetch_price_data(symbol, "1h", start_time_ms, end_time_ms)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50

def main():
    """
    Main function to handle the resolution of the market.
    """
    symbol = "SOLUSDT"
    target_date_str = "2025-06-17"
    target_hour = 14  # 2 PM ET
    
    resolution = resolve_market(symbol, target_date_str, target_hour)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()