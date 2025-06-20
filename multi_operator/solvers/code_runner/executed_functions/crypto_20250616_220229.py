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
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def get_candle_data(symbol, target_datetime):
    """
    Retrieves the closing price for a specific 1-hour candle.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds

    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        # Extract the closing price from the first candle data
        close_price = float(data[0][4])
        return close_price
    else:
        return None

def main():
    # Define the specific date and time for the event
    event_datetime_str = "2025-06-16 17:00:00"
    event_timezone = "US/Eastern"
    symbol = "BTCUSDT"

    # Convert string to datetime object in the specified timezone
    tz = pytz.timezone(event_timezone)
    event_datetime = datetime.strptime(event_datetime_str, "%Y-%m-%d %H:%M:%S")
    event_datetime = tz.localize(event_datetime)

    # Get the closing price of the 1-hour candle starting at the event time
    closing_price_start = get_candle_data(symbol, event_datetime)
    closing_price_end = get_candle_data(symbol, event_datetime + timedelta(hours=1))

    if closing_price_start is not None and closing_price_end is not None:
        # Determine if the price went up or down
        if closing_price_end >= closing_price_start:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 due to data fetch failure

if __name__ == "__main__":
    main()