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
        symbol (str): The symbol to fetch data for, e.g., 'ETHUSDT'.
        interval (str): The interval of the klines data, e.g., '1h'.
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    
    Returns:
        float: The closing price of the symbol at the specified time.
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
        data = response.json()
        return float(data[0][4])  # Closing price
    except Exception as e:
        print(f"Proxy API failed, error: {e}. Falling back to primary API.")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data[0][4])  # Closing price
        except Exception as e:
            print(f"Primary API also failed, error: {e}.")
            return None

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price change of a cryptocurrency on Binance.
    
    Args:
        symbol (str): The cryptocurrency symbol, e.g., 'ETHUSDT'.
        target_datetime (datetime): The datetime for which to check the price.
    
    Returns:
        str: Market resolution as 'p1' for Down, 'p2' for Up, or 'p3' for unknown.
    """
    # Convert target datetime to UTC and milliseconds
    target_datetime_utc = target_datetime.astimezone(pytz.utc)
    start_time_ms = int(target_datetime_utc.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later
    
    # Fetch closing prices at the start and end of the hour
    start_price = fetch_price_data(symbol, "1h", start_time_ms, start_time_ms + 60000)
    end_price = fetch_price_data(symbol, "1h", end_time_ms, end_time_ms + 60000)
    
    if start_price is None or end_price is None:
        return "p3"  # Unknown if any price data is missing
    
    # Determine if the price went up or down
    if end_price >= start_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    # Example: Resolve the market for ETH/USDT on June 13, 2025, at 6 AM ET
    target_datetime = datetime(2025, 6, 13, 6, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    resolution = resolve_market("ETHUSDT", target_datetime)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()