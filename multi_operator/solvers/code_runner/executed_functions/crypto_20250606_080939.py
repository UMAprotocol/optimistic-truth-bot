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
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    headers = {
        "X-MBX-APIKEY": BINANCE_API_KEY
    }

    try:
        # Try fetching data using the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
            raise

def get_close_price(symbol, target_datetime):
    """
    Get the closing price of a cryptocurrency at a specific datetime.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later

    data = fetch_binance_data(symbol, "1m", start_time, end_time)
    if data and len(data) > 0:
        # Extract the close price from the first (and only) entry
        close_price = float(data[0][4])
        return close_price
    else:
        raise ValueError("No data returned from the API.")

def main():
    # Define the target date and time for the price check
    target_datetime = datetime(2025, 6, 6, 8, 0, tzinfo=timezone.utc)
    symbol = "BTCUSDT"
    threshold_price = 252000

    try:
        close_price = get_close_price(symbol, target_datetime)
        print(f"Close price for {symbol} at {target_datetime} UTC: {close_price}")
        if close_price >= threshold_price:
            print("recommendation: p2")  # Yes, price is above or equal to 252,000 USDT
        else:
            print("recommendation: p1")  # No, price is below 252,000 USDT
    except Exception as e:
        print(f"Error fetching price data: {e}")
        print("recommendation: p4")  # Unable to resolve due to error

if __name__ == "__main__":
    main()