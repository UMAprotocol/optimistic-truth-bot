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
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def get_eth_price_at_time(target_datetime):
    """
    Gets the Ethereum price at a specific datetime.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later

    # Fetch price data
    data = fetch_price_data("ETHUSDT", "1h", start_time, end_time)
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    else:
        raise ValueError("No data available for the specified time.")

def main():
    # Define the target datetime for the price check
    target_datetime_str = "2025-06-19 11:00:00"
    target_timezone = pytz.timezone("America/New_York")
    target_datetime = datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S")
    target_datetime = target_timezone.localize(target_datetime)

    try:
        open_price, close_price = get_eth_price_at_time(target_datetime)
        print(f"Open Price: {open_price}, Close Price: {close_price}")
        if close_price >= open_price:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        print(f"Error: {str(e)}")
        print("recommendation: p3")  # Unknown/50-50 if error occurs

if __name__ == "__main__":
    main()