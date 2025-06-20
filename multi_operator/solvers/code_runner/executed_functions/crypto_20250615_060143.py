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
        print(f"Proxy API failed, error: {e}. Falling back to primary API.")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Primary API also failed, error: {e}.")
            raise

def resolve_market(symbol, target_date_str, target_hour):
    """
    Resolves the market based on the price change of a cryptocurrency on Binance.
    
    Args:
        symbol (str): The cryptocurrency symbol (e.g., 'ETHUSDT').
        target_date_str (str): The target date in 'YYYY-MM-DD' format.
        target_hour (int): The hour of the day in 24-hour format.
    
    Returns:
        str: The resolution of the market ('p1', 'p2', or 'p3').
    """
    # Convert target date and hour to the start and end timestamps in UTC
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    target_start = datetime(target_date.year, target_date.month, target_date.day, target_hour, 0, 0, tzinfo=pytz.utc)
    target_end = target_start + timedelta(hours=1)
    
    start_time_ms = int(target_start.timestamp() * 1000)
    end_time_ms = int(target_end.timestamp() * 1000)
    
    # Fetch the price data
    data = fetch_price_data(symbol, "1h", start_time_ms, end_time_ms)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        
        if close_price >= open_price:
            return "p2"  # Market resolves to "Up"
        else:
            return "p1"  # Market resolves to "Down"
    else:
        return "p3"  # Unknown or insufficient data

def main():
    """
    Main function to execute the market resolution logic.
    """
    try:
        resolution = resolve_market("ETHUSDT", "2025-06-15", 1)
        print(f"recommendation: {resolution}")
    except Exception as e:
        print(f"Failed to resolve market due to an error: {e}")
        print("recommendation: p3")  # Default to unknown if there's an error

if __name__ == "__main__":
    main()