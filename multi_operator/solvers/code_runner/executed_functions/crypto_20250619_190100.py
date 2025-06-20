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

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the opening and closing prices of a cryptocurrency.
    
    Args:
        symbol (str): The cryptocurrency symbol (e.g., 'ETHUSDT').
        target_datetime (datetime): The datetime for which the market should be resolved.
    
    Returns:
        str: 'p1' if the price went down, 'p2' if the price went up, 'p3' if unknown.
    """
    # Convert target datetime to UTC and to milliseconds
    target_datetime_utc = target_datetime.astimezone(pytz.utc)
    start_time = int(target_datetime_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later
    
    # Fetch price data
    data = fetch_price_data(symbol, "1h", start_time, end_time)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        
        if close_price > open_price:
            return "p2"  # Up
        elif close_price < open_price:
            return "p1"  # Down
        else:
            return "p3"  # Unknown/50-50
    else:
        return "p3"  # Unknown/50-50 if no data

def main():
    # Example: Resolve for Ethereum on June 19, 2025, 2PM ET
    target_datetime = datetime(2025, 6, 19, 14, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    symbol = "ETHUSDT"
    result = resolve_market(symbol, target_datetime)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()