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
    
    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy failed with error: {e}, falling back to primary API.")
        # Fallback to the primary API endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
            return None

def get_candle_data(symbol, target_datetime):
    """
    Retrieves the closing price of a 1-hour candle for the specified datetime.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds

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
    target_date_str = "2025-06-15"
    target_time_str = "09:00:00"
    timezone_str = "US/Eastern"
    symbol = "BTCUSDT"

    # Parse the target datetime in the specified timezone
    timezone = pytz.timezone(timezone_str)
    target_datetime = timezone.localize(datetime.strptime(f"{target_date_str} {target_time_str}", "%Y-%m-%d %H:%M:%S"))

    # Get the closing price of the 1-hour candle starting at the target datetime
    closing_price_start = get_candle_data(symbol, target_datetime)
    closing_price_end = get_candle_data(symbol, target_datetime + timedelta(hours=1))

    if closing_price_start is None or closing_price_end is None:
        print("recommendation: p4")  # Unable to fetch data
    else:
        # Determine if the price went up or down
        if closing_price_end >= closing_price_start:
            print("recommendation: p2")  # Price went up
        else:
            print("recommendation: p1")  # Price went down

if __name__ == "__main__":
    resolve_market()