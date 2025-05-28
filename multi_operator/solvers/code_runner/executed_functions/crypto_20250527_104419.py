import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_btc_price_at_time(target_datetime):
    """
    Fetches the BTC price at a specific datetime using Binance API.
    
    Args:
        target_datetime (datetime): The datetime at which to fetch the BTC price.
    
    Returns:
        float: The BTC price at the specified datetime or None if an error occurs.
    """
    # Convert datetime to milliseconds since epoch
    timestamp = int(target_datetime.timestamp() * 1000)

    # Prepare parameters for the API request
    params = {
        "symbol": "BTCUSDT",
        "interval": "1m",
        "limit": 1,
        "startTime": timestamp,
        "endTime": timestamp + 60000  # 1 minute later
    }

    # Try fetching from the proxy endpoint first
    try:
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")

    # Fallback to the primary endpoint if proxy fails
    try:
        response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        print(f"Primary endpoint also failed: {str(e)}")
        return None

def main():
    # Define the target datetime in Beijing time
    beijing_tz = pytz.timezone("Asia/Shanghai")
    target_datetime = datetime(2025, 5, 27, 23, 0, tzinfo=beijing_tz)
    
    # Convert Beijing time to UTC
    target_datetime_utc = target_datetime.astimezone(pytz.utc)

    # Fetch the BTC price at the specified time
    btc_price = fetch_btc_price_at_time(target_datetime_utc)

    # Determine the resolution based on the fetched price
    if btc_price is None:
        print("recommendation: p4")  # Unable to fetch the price
    elif btc_price > 150000:
        print("recommendation: p1")  # BTC price exceeds 150000 USD
    else:
        print("recommendation: p2")  # BTC price does not exceed 150000 USD

if __name__ == "__main__":
    main()