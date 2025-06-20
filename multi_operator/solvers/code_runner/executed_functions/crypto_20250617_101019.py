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
    Fetches price data from Binance using the proxy endpoint with a fallback to the primary endpoint.
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
        return data
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fallback to the primary endpoint
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data

def get_eth_price_change():
    """
    Determines if the ETH price went up or down based on the 1-hour candle starting at June 17, 5 AM ET.
    """
    # Convert ET time to UTC
    et_timezone = pytz.timezone("US/Eastern")
    utc_timezone = pytz.utc
    target_time_et = et_timezone.localize(datetime(2025, 6, 17, 5, 0, 0))
    target_time_utc = target_time_et.astimezone(utc_timezone)
    
    # Convert datetime to milliseconds since epoch
    start_time = int(target_time_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later
    
    # Fetch price data
    data = fetch_price_data("ETHUSDT", "1h", start_time, end_time)
    
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change = close_price - open_price
        
        if price_change >= 0:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 if no data available

def main():
    """
    Main function to determine the price movement of Ethereum on a specific date and time.
    """
    result = get_eth_price_change()
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()