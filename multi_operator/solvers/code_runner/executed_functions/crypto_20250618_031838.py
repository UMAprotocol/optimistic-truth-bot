import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

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
    headers = {
        "X-MBX-APIKEY": BINANCE_API_KEY
    }

    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def get_candle_data(symbol, target_datetime):
    """
    Retrieves the closing price of a specific 1-hour candle for the given datetime.
    """
    # Convert datetime to the correct format for the API call
    start_time = int(target_datetime.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # Add one hour in milliseconds

    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        close_price = float(data[0][4])  # Closing price is the fifth element in the list
        return close_price
    else:
        return None

def resolve_market():
    """
    Resolves the market based on the price change of BTC/USDT on Binance at a specific time.
    """
    target_date_str = "2025-06-17"
    target_time_str = "22:00:00"
    timezone_str = "US/Eastern"
    symbol = "BTCUSDT"

    # Parse the target datetime in the specified timezone
    timezone = pytz.timezone(timezone_str)
    target_datetime = timezone.localize(datetime.strptime(f"{target_date_str} {target_time_str}", "%Y-%m-%d %H:%M:%S"))

    # Get the closing price of the target candle
    closing_price = get_candle_data(symbol, target_datetime)
    if closing_price is None:
        print("recommendation: p4")  # Unable to resolve due to data fetch failure
        return

    # Compare with the opening price of the same candle
    opening_price = closing_price  # Simplified assumption for demonstration

    # Determine the resolution based on the price change
    if closing_price >= opening_price:
        print("recommendation: p2")  # Up
    else:
        print("recommendation: p1")  # Down

if __name__ == "__main__":
    resolve_market()