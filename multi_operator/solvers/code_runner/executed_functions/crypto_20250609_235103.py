import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_URL = "https://api.binance.com/api/v3"

def get_data(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint.
    """
    try:
        # First try the proxy endpoint
        response = requests.get(f"{PROXY_URL}?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            return data[0][4]  # Close price of the candle
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{PRIMARY_URL}/klines", params={
            "symbol": symbol,
            "interval": "1m",
            "limit": 1,
            "startTime": start_time,
            "endTime": end_time
        }, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            return data[0][4]  # Close price of the candle
    return None

def check_price_threshold(symbol, start_date, end_date, threshold):
    """
    Checks if the price of a symbol has reached a certain threshold between two dates.
    """
    # Convert dates to milliseconds since the epoch
    start_dt = datetime.strptime(start_date, "%Y-%m-%d %H:%M")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d %H:%M")
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(start_dt).astimezone(pytz.utc)
    end_dt = tz.localize(end_dt).astimezone(pytz.utc)
    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = int(end_dt.timestamp() * 1000)

    # Check prices over the range
    current_time = start_ms
    while current_time <= end_ms:
        price = get_data(symbol, current_time, current_time + 60000)  # Check one minute interval
        if price and float(price) >= threshold:
            return True
        current_time += 60000  # Move to the next minute
    return False

def main():
    """
    Main function to determine if the price of HOUSE/SOL reached $0.300 between May 7, 2025, 15:00 and May 31, 2025, 23:59.
    """
    symbol = "HOUSEUSDT"
    start_date = "2025-05-07 15:00"
    end_date = "2025-05-31 23:59"
    threshold = 0.300
    if check_price_threshold(symbol, start_date, end_date, threshold):
        print("recommendation: p2")  # Yes, it reached $0.300
    else:
        print("recommendation: p1")  # No, it did not reach $0.300

if __name__ == "__main__":
    main()