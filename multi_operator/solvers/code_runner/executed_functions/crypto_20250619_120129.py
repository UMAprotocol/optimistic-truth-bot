import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, start_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
    
    Args:
        symbol (str): The symbol to fetch data for.
        start_time (int): The start time in milliseconds for the data.
    
    Returns:
        float: The closing price of the symbol at the specified time.
    """
    params = {
        "symbol": symbol,
        "interval": "1h",
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later
    }

    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Closing price
    except Exception as e:
        print(f"Proxy failed with error: {e}, trying primary API.")
        # Fallback to the primary API endpoint
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data[0][4])  # Closing price
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
            raise

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price movement of the symbol from the open to close of a specified hour.
    
    Args:
        symbol (str): The trading symbol.
        target_datetime (datetime): The datetime for which the market should be resolved.
    
    Returns:
        str: The market resolution recommendation.
    """
    # Convert datetime to UTC and to milliseconds
    utc_datetime = target_datetime.astimezone(pytz.utc)
    start_time_ms = int(utc_datetime.timestamp() * 1000)

    # Fetch the closing price at the specified time
    closing_price = fetch_price_data(symbol, start_time_ms)

    # Fetch the opening price at the specified time
    opening_price = fetch_price_data(symbol, start_time_ms)

    # Determine the market resolution
    if closing_price >= opening_price:
        return "recommendation: p2"  # Up
    else:
        return "recommendation: p1"  # Down

def main():
    # Example usage
    target_datetime = datetime(2025, 6, 19, 7, 0, tzinfo=pytz.timezone("US/Eastern"))
    symbol = "BTCUSDT"
    try:
        result = resolve_market(symbol, target_datetime)
        print(result)
    except Exception as e:
        print(f"Failed to resolve market due to error: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()