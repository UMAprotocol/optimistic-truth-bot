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
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
    
    Args:
        symbol (str): The symbol to fetch data for (e.g., 'ETHUSDT').
        interval (str): The interval of the klines data (e.g., '1h').
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
        # Try fetching data from the proxy API first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Proxy API failed: {e}, falling back to primary API")
        # Fallback to the primary API if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market(symbol, target_date_str, target_hour):
    """
    Resolves the market based on the opening and closing prices of a specific hour candle.
    
    Args:
        symbol (str): The trading symbol (e.g., 'ETHUSDT').
        target_date_str (str): The target date in 'YYYY-MM-DD' format.
        target_hour (int): The hour of the day for which the candle is considered.
    
    Returns:
        str: The resolution of the market ('p1' for down, 'p2' for up, 'p3' for unknown).
    """
    # Convert the target date and hour to UTC timestamp
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    target_datetime = target_date.replace(hour=target_hour)
    target_datetime_utc = target_datetime.astimezone(pytz.utc)
    
    start_time_ms = int(target_datetime_utc.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later in milliseconds
    
    # Fetch the price data
    data = fetch_price_data(symbol, "1h", start_time_ms, end_time_ms)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        
        if close_price >= open_price:
            return "p2"  # Market resolves to 'Up'
        else:
            return "p1"  # Market resolves to 'Down'
    else:
        return "p3"  # Market resolves to 'unknown/50-50' if no data available

def main():
    # Example usage
    resolution = resolve_market("ETHUSDT", "2025-06-19", 11)  # June 19, 2025 at 11 AM UTC
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()