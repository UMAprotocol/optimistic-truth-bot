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
        # Try fetching data from the proxy endpoint
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
    # Convert datetime to milliseconds
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        # Extract the close price from the first candle data
        close_price = float(data[0][4])
        return close_price
    else:
        return None

def resolve_market():
    """
    Resolves the market based on the price change of BTC/USDT on Binance.
    """
    target_date_str = "2025-06-17"
    target_time_str = "19:00:00"
    timezone_str = "US/Eastern"
    symbol = "BTCUSDT"

    # Parse the target datetime in the specified timezone
    tz = pytz.timezone(timezone_str)
    target_datetime = datetime.strptime(f"{target_date_str} {target_time_str}", "%Y-%m-%d %H:%M:%S")
    target_datetime = tz.localize(target_datetime)

    # Get the closing price of the target 1-hour candle
    close_price_start = get_candle_data(symbol, target_datetime)
    close_price_end = get_candle_data(symbol, target_datetime + timedelta(hours=1))

    if close_price_start is None or close_price_end is None:
        print("recommendation: p4")  # Unable to resolve due to data fetch failure
    else:
        # Calculate the percentage change
        percentage_change = ((close_price_end - close_price_start) / close_price_start) * 100

        # Resolve based on the percentage change
        if percentage_change >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down

if __name__ == "__main__":
    resolve_market()