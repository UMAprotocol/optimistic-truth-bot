import requests
import os
from datetime import datetime
from dotenv import load_dotenv
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
    Fetches price data from Binance using the proxy API with a fallback to the primary API.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching from proxy API
        response = requests.get(f"{PROXY_API}?symbol={symbol}&interval={interval}&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy API.")
        return data
    except Exception as e:
        logging.warning(f"Proxy API failed: {e}. Attempting primary API.")
        # Fallback to primary API
        response = requests.get(f"{PRIMARY_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from primary API.")
        return data

def resolve_market(symbol, target_date_str):
    """
    Resolves the market based on the opening and closing prices of the specified symbol on the target date.
    """
    # Convert date string to UTC timestamp for the start of the hour
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d %H:%M:%S")
    tz = pytz.timezone("America/New_York")  # Market specifies ET
    target_date = tz.localize(target_date)
    start_time = int(target_date.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour in milliseconds

    # Fetch price data
    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        logging.info(f"Open price: {open_price}, Close price: {close_price}")

        # Determine market resolution
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50

def main():
    """
    Main function to handle the resolution of the Ethereum market for June 20, 12AM ET.
    """
    symbol = "ETHUSDT"
    target_date_str = "2025-06-20 00:00:00"
    result = resolve_market(symbol, target_date_str)
    print(result)

if __name__ == "__main__":
    main()