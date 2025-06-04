import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": "1h",
        "startTime": start_time,
        "endTime": end_time
    }
    headers = {
        "X-MBX-APIKEY": BINANCE_API_KEY
    }

    try:
        # Try proxy endpoint first
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()

def get_price_change(data):
    """
    Calculate the percentage change from open to close price from the data.
    """
    if not data or len(data) == 0:
        return None
    open_price = float(data[0][1])
    close_price = float(data[0][4])
    return ((close_price - open_price) / open_price) * 100

def main():
    # Define the specific date and time for the event
    event_date = "2025-06-04"
    event_time = "05:00:00"
    event_datetime_str = f"{event_date} {event_time} ET"
    event_datetime = datetime.strptime(event_datetime_str, "%Y-%m-%d %H:%M:%S %Z")
    event_timestamp_utc = int(pytz.timezone("US/Eastern").localize(event_datetime).timestamp() * 1000)

    # Fetch data for the specific hour candle
    data = fetch_binance_data("BTCUSDT", event_timestamp_utc, event_timestamp_utc + 3600000)

    # Calculate the price change
    price_change = get_price_change(data)

    # Determine the resolution based on the price change
    if price_change is None:
        print("recommendation: p4")  # Unable to determine
    elif price_change >= 0:
        print("recommendation: p2")  # Market resolves to "Up"
    else:
        print("recommendation: p1")  # Market resolves to "Down"

if __name__ == "__main__":
    main()