import requests
import os
from datetime import datetime
from pytz import timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_eth_price(date_str, hour):
    """
    Fetches the ETH/USDT price for a specific hour on a given date from Binance.
    Args:
        date_str (str): Date in 'YYYY-MM-DD' format.
        hour (int): Hour in 24-hour format.
    Returns:
        tuple: (open_price, close_price)
    """
    # Convert local time to UTC
    et = timezone('US/Eastern')
    utc = timezone('UTC')
    naive_dt = datetime.strptime(f"{date_str} {hour}:00:00", "%Y-%m-%d %H:%M:%S")
    local_dt = et.localize(naive_dt)
    utc_dt = local_dt.astimezone(utc)

    # Convert datetime to milliseconds since epoch
    start_time = int(utc_dt.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Construct the URL and parameters for the API request
    params = {
        "symbol": "ETHUSDT",
        "interval": "1h",
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
    }

    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Proxy failed, error: {e}, trying primary endpoint.")
        # Fallback to the primary endpoint if proxy fails
        response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params)
        response.raise_for_status()
        data = response.json()

    # Extract open and close prices from the data
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return (open_price, close_price)
    else:
        raise ValueError("No data available for the specified time and date.")

def main():
    # Specific date and time for the market resolution
    date_str = "2025-06-19"
    hour = 16  # 4 PM ET

    try:
        open_price, close_price = fetch_eth_price(date_str, hour)
        if close_price >= open_price:
            print("recommendation: p2")  # Market resolves to "Up"
        else:
            print("recommendation: p1")  # Market resolves to "Down"
    except Exception as e:
        print(f"Failed to fetch prices: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    main()