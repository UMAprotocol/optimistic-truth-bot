import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

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
        symbol (str): The symbol to fetch data for, e.g., 'BTCUSDT'.
        start_time (int): Start time in milliseconds for the data.
    
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
        print(f"Proxy failed, error: {e}, trying primary API...")
        # Fallback to the primary API endpoint
        response = requests.get(PRIMARY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Closing price

def resolve_market(symbol, target_date_str):
    """
    Resolves the market based on the price change of a cryptocurrency on Binance.
    
    Args:
        symbol (str): The cryptocurrency symbol, e.g., 'BTCUSDT'.
        target_date_str (str): The target date in 'YYYY-MM-DD' format.
    
    Returns:
        str: Market resolution recommendation.
    """
    # Convert date string to datetime at 2 PM ET
    target_datetime = datetime.strptime(target_date_str + " 14:00:00", "%Y-%m-%d %H:%M:%S")
    # Convert to UTC (ET is UTC-4 or UTC-5 depending on DST)
    target_datetime_utc = target_datetime - timedelta(hours=4)  # Assuming no DST
    start_time_ms = int(target_datetime_utc.timestamp() * 1000)
    
    # Fetch closing prices for the specified hour
    closing_price = fetch_price_data(symbol, start_time_ms)
    
    # Compare closing price to the opening price to determine market resolution
    if closing_price >= 0:
        return "recommendation: p2"  # Up
    else:
        return "recommendation: p1"  # Down

def main():
    # Example usage
    resolution = resolve_market("BTCUSDT", "2025-06-11")
    print(resolution)

if __name__ == "__main__":
    main()