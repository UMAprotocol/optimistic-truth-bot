import requests
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_eth_price():
    """
    Fetches the Ethereum price at a specific time from Binance using both the primary and proxy endpoints.
    """
    # Define the specific time and symbol
    symbol = "ETHUSDT"
    interval = "1m"
    limit = 1
    # Convert local time to UTC timestamp in milliseconds
    target_time = datetime(2025, 4, 18, 16, 0, 0, tzinfo=timezone.utc)  # 12:00 PM ET in UTC
    start_time = int(target_time.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later

    # Prepare the request parameters
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
        "startTime": start_time,
        "endTime": end_time
    }

    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            close_price = float(data[0][4])
            return close_price
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def main():
    """
    Main function to determine if Ethereum was above $1,600 on April 18, 2025 at 12:00 PM ET.
    """
    close_price = fetch_eth_price()
    if close_price is None:
        print("recommendation: p3")  # Unknown/50-50 if data fetching fails
    elif close_price >= 1600.01:
        print("recommendation: p2")  # Yes, Ethereum was above $1,600
    else:
        print("recommendation: p1")  # No, Ethereum was not above $1,600

if __name__ == "__main__":
    main()