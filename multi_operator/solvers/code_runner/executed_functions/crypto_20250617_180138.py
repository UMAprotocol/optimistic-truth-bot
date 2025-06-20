import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

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
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def get_price_change(symbol, target_datetime):
    """
    Calculates the price change for the specified symbol at the target datetime.
    """
    # Convert target datetime to UTC timestamp in milliseconds
    target_timestamp_utc = int(target_datetime.timestamp() * 1000)
    
    # Fetch price data for the 1 hour interval starting at the target datetime
    data = fetch_price_data(symbol, "1h", target_timestamp_utc, target_timestamp_utc + 3600000)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change_percentage = ((close_price - open_price) / open_price) * 100
        return price_change_percentage
    else:
        return None

def main():
    """
    Main function to determine if the Bitcoin price went up or down at the specified time.
    """
    # Define the target datetime in Eastern Time
    target_datetime_str = "2025-06-17 13:00:00"
    eastern = pytz.timezone("US/Eastern")
    target_datetime = eastern.localize(datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S"))
    
    # Convert to UTC
    target_datetime_utc = target_datetime.astimezone(pytz.utc)
    
    # Get the price change percentage
    price_change_percentage = get_price_change("BTCUSDT", target_datetime_utc)
    
    if price_change_percentage is not None:
        if price_change_percentage >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50

if __name__ == "__main__":
    main()