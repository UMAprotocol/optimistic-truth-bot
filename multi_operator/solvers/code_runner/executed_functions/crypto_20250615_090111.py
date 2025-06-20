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
        # Try fetching from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Closing price
    except Exception as e:
        print(f"Proxy failed with error: {e}, trying primary API.")
        # Fallback to the primary API endpoint
        response = requests.get(PRIMARY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Closing price

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price change of a cryptocurrency.
    
    Args:
        symbol (str): The cryptocurrency symbol.
        target_datetime (datetime): The datetime for which to check the price.
    
    Returns:
        str: Market resolution recommendation.
    """
    # Convert datetime to UTC and then to milliseconds
    utc_datetime = target_datetime.astimezone(pytz.utc)
    start_time_ms = int(utc_datetime.timestamp() * 1000)

    # Fetch closing prices for the specified hour
    closing_price = fetch_price_data(symbol, start_time_ms)

    # Fetch closing price for the hour before to compare
    previous_closing_price = fetch_price_data(symbol, start_time_ms - 3600000)

    # Determine market resolution
    if closing_price >= previous_closing_price:
        return "recommendation: p2"  # Up
    else:
        return "recommendation: p1"  # Down

def main():
    # Example usage
    symbol = "ETHUSDT"
    target_datetime = datetime(2025, 6, 15, 4, 0, tzinfo=pytz.timezone("US/Eastern"))
    result = resolve_market(symbol, target_datetime)
    print(result)

if __name__ == "__main__":
    main()