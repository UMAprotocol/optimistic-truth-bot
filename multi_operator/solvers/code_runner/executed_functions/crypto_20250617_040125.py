import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"

def fetch_eth_price(date_time_str):
    """
    Fetches the closing price of the ETH/USDT pair for a specific 1-hour candle on Binance.
    
    Args:
        date_time_str (str): The date and time string in 'YYYY-MM-DD HH:MM' format (ET timezone).
    
    Returns:
        float: The closing price of the candle.
    """
    # Convert ET time to UTC
    et_timezone = pytz.timezone('US/Eastern')
    utc_timezone = pytz.utc
    local_dt = et_timezone.localize(datetime.strptime(date_time_str, '%Y-%m-%d %H:%M'))
    utc_dt = local_dt.astimezone(utc_timezone)
    
    # Calculate start and end times in milliseconds
    start_time = int(utc_dt.timestamp() * 1000)
    end_time = int((utc_dt + timedelta(hours=1)).timestamp() * 1000)
    
    # Prepare API request
    params = {
        'symbol': 'ETHUSDT',
        'interval': '1h',
        'startTime': start_time,
        'endTime': end_time,
        'limit': 1
    }
    
    # Try fetching from the proxy endpoint first
    try:
        response = requests.get(f"{PROXY_ENDPOINT}/api/v3/klines", params=params)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Closing price
    except Exception as e:
        print(f"Proxy failed with error: {e}, trying primary endpoint.")
        # Fallback to the primary endpoint
        try:
            response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params)
            response.raise_for_status()
            data = response.json()
            return float(data[0][4])  # Closing price
        except Exception as e:
            print(f"Primary endpoint failed with error: {e}")
            return None

def main():
    # Specific date and time for the market resolution
    date_time_str = '2025-06-16 23:00'  # 11 PM ET
    closing_price_start = fetch_eth_price(date_time_str)
    closing_price_end = fetch_eth_price('2025-06-17 00:00')  # 12 AM ET next day
    
    if closing_price_start is not None and closing_price_end is not None:
        if closing_price_end >= closing_price_start:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 if data fetching failed

if __name__ == "__main__":
    main()