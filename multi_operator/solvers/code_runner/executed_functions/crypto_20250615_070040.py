import requests
import os
from datetime import datetime, timedelta
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
        # Try fetching from proxy first
        response = requests.get(f"{PROXY_API}?symbol={symbol}&interval={interval}&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logging.warning(f"Proxy failed, error: {e}. Trying primary API.")
        # Fallback to primary API if proxy fails
        response = requests.get(f"{PRIMARY_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from primary API.")
        return data

def get_candle_data(symbol, target_datetime):
    """
    Get the closing price of a specific 1-hour candle.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        close_price = float(data[0][4])  # Closing price is the fifth element
        return close_price
    else:
        raise ValueError("No data available for the specified time.")

def main():
    """
    Main function to determine if the Bitcoin price went up or down.
    """
    # Define the specific date and time
    target_date_str = "2025-06-15"
    target_time_str = "02:00:00"
    timezone_str = "US/Eastern"
    
    # Convert to datetime object
    target_datetime = datetime.strptime(f"{target_date_str} {target_time_str}", "%Y-%m-%d %H:%M:%S")
    target_datetime = pytz.timezone(timezone_str).localize(target_datetime)
    
    # Convert to UTC
    target_datetime_utc = target_datetime.astimezone(pytz.utc)
    
    # Get the closing price for the specified hour
    try:
        close_price_start = get_candle_data("BTCUSDT", target_datetime_utc)
        close_price_end = get_candle_data("BTCUSDT", target_datetime_utc + timedelta(hours=1))
        
        # Determine if the price went up or down
        if close_price_end >= close_price_start:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        logging.error(f"Error fetching data: {e}")
        print("recommendation: p3")  # Unknown/50-50 if error occurs

if __name__ == "__main__":
    main()