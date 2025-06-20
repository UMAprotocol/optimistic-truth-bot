import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_ethusdt_price_change(date_str, hour):
    """
    Fetches the percentage change for the ETHUSDT pair for a specific hour candle on Binance.

    Args:
        date_str (str): Date in YYYY-MM-DD format.
        hour (int): Hour of the day for the 1-hour candle (24-hour format).

    Returns:
        float: The percentage change of the ETHUSDT pair.
    """
    # Convert date and hour to the start and end timestamps of the 1-hour candle
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    dt = dt.replace(hour=hour, minute=0, second=0, microsecond=0)
    start_time = int(dt.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # Add one hour in milliseconds

    # Construct the query parameters
    params = {
        "symbol": "ETHUSDT",
        "interval": "1h",
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
    }

    try:
        # First try the proxy endpoint
        response = requests.get(f"{PROXY_API_URL}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{PRIMARY_API_URL}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

    if not data:
        raise ValueError("No data returned from Binance API.")

    # Extract the close and open prices from the data
    open_price = float(data[0][1])
    close_price = float(data[0][4])

    # Calculate the percentage change
    percentage_change = ((close_price - open_price) / open_price) * 100

    return percentage_change

def main():
    # Specific date and time for the market resolution
    date_str = "2025-06-11"
    hour = 21  # 9 PM ET, assuming the server is in ET

    try:
        change = fetch_ethusdt_price_change(date_str, hour)
        if change >= 0:
            print("recommendation: p2")  # Market resolves to "Up"
        else:
            print("recommendation: p1")  # Market resolves to "Down"
    except Exception as e:
        print(f"Error fetching data: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    main()