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
        float: The closing price of the interval.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Closing price
    except Exception as e:
        print(f"Proxy failed, error: {e}, trying primary API...")
        # Fallback to the primary API endpoint
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data[0][4])  # Closing price
        except Exception as e:
            print(f"Primary API failed, error: {e}")
            raise

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price change of the cryptocurrency.
    
    Args:
        symbol (str): The cryptocurrency symbol (e.g., 'ETHUSDT').
        target_datetime (datetime): The datetime for which to check the price.
    
    Returns:
        str: 'p1' if price is down, 'p2' if price is up, 'p3' if unknown.
    """
    # Convert target datetime to UTC and milliseconds
    target_datetime_utc = target_datetime.astimezone(pytz.utc)
    start_time_ms = int(target_datetime_utc.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later
    
    try:
        start_price = fetch_price_data(symbol, "1h", start_time_ms, start_time_ms + 60000)  # Start of the hour
        end_price = fetch_price_data(symbol, "1h", end_time_ms - 60000, end_time_ms)  # End of the hour
        
        if end_price >= start_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    except Exception as e:
        print(f"Error resolving market: {e}")
        return "p3"  # Unknown

def main():
    # Example usage
    symbol = "ETHUSDT"
    target_datetime = datetime(2025, 6, 12, 5, 0, tzinfo=pytz.timezone("US/Eastern"))
    result = resolve_market(symbol, target_datetime)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()