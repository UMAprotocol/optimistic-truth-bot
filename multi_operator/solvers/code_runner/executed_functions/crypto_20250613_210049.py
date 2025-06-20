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

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
    
    Args:
        symbol (str): The symbol to fetch data for, e.g., 'ETHUSDT'.
        interval (str): The interval of the candlestick data, e.g., '1h'.
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    
    Returns:
        float: The closing price of the candlestick.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
    }
    
    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(f"{PROXY_API_URL}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Closing price
    except Exception as e:
        print(f"Proxy failed, error: {e}, trying primary API")
        # Fallback to the primary API endpoint
        try:
            response = requests.get(f"{PRIMARY_API_URL}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data[0][4])  # Closing price
        except Exception as e:
            print(f"Primary API failed, error: {e}")
            raise

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price change of a cryptocurrency on Binance.
    
    Args:
        symbol (str): The cryptocurrency symbol, e.g., 'ETHUSDT'.
        target_datetime (datetime): The datetime for which to check the price.
    
    Returns:
        str: 'p1' if price is down, 'p2' if price is up, 'p3' if unknown.
    """
    # Convert target datetime to UTC and milliseconds
    target_time_utc = target_datetime.astimezone(pytz.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later
    
    try:
        # Fetch closing prices at the start and end of the hour
        start_price = fetch_price_data(symbol, "1h", start_time_ms, start_time_ms)
        end_price = fetch_price_data(symbol, "1h", end_time_ms, end_time_ms)
        
        # Determine if the price went up or down
        if end_price >= start_price:
            return "p2"  # Price went up
        else:
            return "p1"  # Price went down
    except Exception as e:
        print(f"Error resolving market: {e}")
        return "p3"  # Unknown or error

def main():
    # Example usage
    target_datetime = datetime(2025, 6, 13, 16, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    symbol = "ETHUSDT"
    result = resolve_market(symbol, target_datetime)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()