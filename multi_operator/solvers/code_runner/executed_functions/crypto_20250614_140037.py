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
        symbol (str): The symbol to fetch data for, e.g., 'BTCUSDT'.
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
            raise

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price change of a cryptocurrency on Binance.
    
    Args:
        symbol (str): The cryptocurrency symbol, e.g., 'BTCUSDT'.
        target_datetime (datetime): The datetime for which the price change is to be evaluated.
    
    Returns:
        str: 'p1' if the price is down, 'p2' if the price is up, 'p3' if unknown.
    """
    # Convert target datetime to UTC and to milliseconds
    target_datetime_utc = target_datetime.astimezone(pytz.utc)
    start_time_ms = int(target_datetime_utc.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later

    # Fetch closing prices at the start and end of the interval
    try:
        start_price = fetch_price_data(symbol, "1h", start_time_ms, start_time_ms)
        end_price = fetch_price_data(symbol, "1h", end_time_ms, end_time_ms)
        
        if end_price >= start_price:
            return "p2"  # Price went up
        else:
            return "p1"  # Price went down
    except Exception as e:
        print(f"Error resolving market: {e}")
        return "p3"  # Unknown or error

def main():
    # Example usage
    symbol = "BTCUSDT"
    target_datetime = datetime(2025, 6, 14, 9, 0, tzinfo=pytz.timezone("US/Eastern"))
    result = resolve_market(symbol, target_datetime)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()