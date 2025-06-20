import requests
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_eth_price(target_time):
    """
    Fetch the Ethereum price at a specific time using Binance API.
    
    Args:
        target_time (datetime): The target datetime object in UTC.
    
    Returns:
        float: The closing price of Ethereum at the specified time.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_time.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later

    # Parameters for the API request
    params = {
        "symbol": "ETHUSDT",
        "interval": "1m",
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
            return float(data[0][4])  # Closing price
    except Exception as e:
        print(f"Proxy failed, error: {e}, trying primary API.")
        try:
            # Fallback to the primary API endpoint
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Closing price
        except Exception as e:
            print(f"Primary API also failed, error: {e}")
            return None

def main():
    # Define the target time in Eastern Time
    et_timezone = pytz.timezone("US/Eastern")
    target_time_et = et_timezone.localize(datetime(2025, 6, 10, 12, 0))  # June 10, 2025, 12:00 ET
    target_time_utc = target_time_et.astimezone(pytz.utc)

    # Fetch the Ethereum price at the specified time
    eth_price = fetch_eth_price(target_time_utc)

    # Check if the price is above $2,700
    if eth_price is not None:
        if eth_price > 2700:
            print("recommendation: p2")  # Yes
        else:
            print("recommendation: p1")  # No
    else:
        print("recommendation: p3")  # Unknown/50-50 due to API failure

if __name__ == "__main__":
    main()