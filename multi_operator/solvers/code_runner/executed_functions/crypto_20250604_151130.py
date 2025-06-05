import requests
import logging
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_data(symbol, start_time, end_time):
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"
    
    try:
        # First try the proxy endpoint
        response = requests.get(f"{proxy_url}?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Close price
    except Exception as e:
        logging.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Close price

def convert_to_utc_timestamp(date_str, hour, minute, timezone_str):
    tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S")
    local_datetime = tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    return int(utc_datetime.timestamp() * 1000)

def main():
    # Define the dates and times for price comparison
    date1 = "2025-05-31"
    date2 = "2025-06-01"
    hour = 12
    minute = 0
    timezone_str = "US/Eastern"
    symbol = "BTCUSDT"
    
    # Convert dates and times to UTC timestamps
    start_time1 = convert_to_utc_timestamp(date1, hour, minute, timezone_str)
    start_time2 = convert_to_utc_timestamp(date2, hour, minute, timezone_str)
    
    # Get close prices for both dates
    close_price1 = get_data(symbol, start_time1, start_time1 + 60000)
    close_price2 = get_data(symbol, start_time2, start_time2 + 60000)
    
    # Determine the resolution based on the close prices
    if close_price1 < close_price2:
        recommendation = "p2"  # Up
    elif close_price1 > close_price2:
        recommendation = "p1"  # Down
    else:
        recommendation = "p3"  # 50-50
    
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()