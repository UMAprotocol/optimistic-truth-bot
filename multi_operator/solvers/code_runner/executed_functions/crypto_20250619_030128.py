import requests
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os
import logging

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_binance_data(symbol, interval, start_time):
    """
    Fetches data from Binance API with a fallback to a proxy if the primary endpoint fails.
    """
    primary_url = "https://api.binance.com/api/v3/klines"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later
    }
    
    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        logging.info(f"Proxy failed, trying primary endpoint: {e}")
        # Fallback to primary endpoint
        response = requests.get(primary_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data

def resolve_market(symbol, target_date_str, target_hour):
    """
    Resolves the market based on the opening and closing prices of the specified candle.
    """
    # Convert target time to UTC timestamp
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    target_date = target_date.replace(hour=target_hour, tzinfo=pytz.timezone("US/Eastern"))
    target_date_utc = target_date.astimezone(pytz.utc)
    start_time = int(target_date_utc.timestamp() * 1000)  # Convert to milliseconds
    
    # Fetch data
    data = get_binance_data(symbol, "1h", start_time)
    
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 if no data

def main():
    """
    Main function to handle the resolution of the market.
    """
    symbol = "BTCUSDT"
    target_date_str = "2025-06-18"
    target_hour = 22  # 10 PM ET
    
    result = resolve_market(symbol, target_date_str, target_hour)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()