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

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary request fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data using the proxy URL first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy request failed: {e}, falling back to primary API.")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary API request also failed: {e}")
            return None

def get_close_price(symbol, target_datetime):
    """
    Retrieves the closing price of a cryptocurrency at a specific datetime.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later

    data = fetch_binance_data(symbol, "1m", start_time, end_time)
    if data and len(data) > 0:
        close_price = float(data[0][4])  # Closing price is the fifth element in the list
        return close_price
    else:
        return None

def main():
    # Define the target date and time for the query
    target_datetime = datetime(2025, 6, 5, 10, 0, tzinfo=timezone.utc)
    symbol = "BTCUSDT"
    threshold_price = 252000

    # Get the close price at the specified datetime
    close_price = get_close_price(symbol, target_datetime)

    if close_price is not None:
        if close_price >= threshold_price:
            print("recommendation: p2")  # Yes, price is above or equal to 252,000 USDT
        else:
            print("recommendation: p1")  # No, price is below 252,000 USDT
    else:
        print("recommendation: p4")  # Unable to determine due to API failure or no data

if __name__ == "__main__":
    main()