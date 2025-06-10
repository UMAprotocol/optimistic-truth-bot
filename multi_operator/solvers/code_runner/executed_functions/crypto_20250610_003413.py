import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz
import logging

# Load environment variables
load_dotenv()

# API keys
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API = "https://api.binance.com/api/v3"
PROXY_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        # Try fetching from proxy API first
        response = requests.get(f"{PROXY_API}?symbol={symbol}&interval={interval}&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy API.")
        return data
    except Exception as e:
        logging.error(f"Proxy API failed: {e}, trying primary API.")
        # Fallback to primary API if proxy fails
        response = requests.get(f"{PRIMARY_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from primary API.")
        return data

def get_candle_data(symbol, date_str, hour):
    """
    Get the closing price of the 1-hour candle for the given symbol, date, and hour.
    """
    # Convert local time to UTC
    local_time = datetime.strptime(f"{date_str} {hour}:00:00", "%Y-%m-%d %H:%M:%S")
    local_time = pytz.timezone("America/New_York").localize(local_time)
    utc_time = local_time.astimezone(pytz.utc)

    # Calculate start and end times in milliseconds
    start_time = int(utc_time.timestamp() * 1000)
    end_time = int((utc_time + timedelta(hours=1)).timestamp() * 1000)

    # Fetch candle data
    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    else:
        logging.error("No data available for the specified time.")
        return None, None

def resolve_market(open_price, close_price):
    """
    Resolve the market based on the price movement.
    """
    if close_price is None or open_price is None:
        return "p3"  # Unknown or no data
    if close_price >= open_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    symbol = "BTCUSDT"
    date_str = "2025-05-30"
    hour = 22  # 10 PM ET

    open_price, close_price = get_candle_data(symbol, date_str, hour)
    result = resolve_market(open_price, close_price)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()