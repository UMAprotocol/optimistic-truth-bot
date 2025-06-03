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
PRIMARY_API_URL = "https://api.binance.com/api/v3"
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
        response = requests.get(f"{PROXY_API_URL}/klines", params=params)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Closing price
    except Exception as e:
        print(f"Proxy failed, error: {e}, trying primary API...")
        try:
            # Fallback to the primary API endpoint
            response = requests.get(f"{PRIMARY_API_URL}/klines", params=params)
            response.raise_for_status()
            data = response.json()
            return float(data[0][4])  # Closing price
        except Exception as e:
            print(f"Primary API failed, error: {e}")
            return None

def resolve_market():
    """
    Resolves the market based on the price change of BTC/USDT on Binance.
    
    Returns:
        str: The market resolution recommendation.
    """
    # Define the date and time for the query
    target_date = datetime(2025, 6, 2, 11, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    target_time_utc = target_date.astimezone(pytz.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)
    
    # Fetch the closing price at the specified time
    closing_price = fetch_price_data("BTCUSDT", start_time_ms)
    
    if closing_price is None:
        return "recommendation: p3"  # Unknown or API failure
    
    # Fetch the closing price one hour later
    closing_price_one_hour_later = fetch_price_data("BTCUSDT", start_time_ms + 3600000)
    
    if closing_price_one_hour_later is None:
        return "recommendation: p3"  # Unknown or API failure
    
    # Determine if the price went up or down
    if closing_price_one_hour_later >= closing_price:
        return "recommendation: p2"  # Up
    else:
        return "recommendation: p1"  # Down

if __name__ == "__main__":
    result = resolve_market()
    print(result)