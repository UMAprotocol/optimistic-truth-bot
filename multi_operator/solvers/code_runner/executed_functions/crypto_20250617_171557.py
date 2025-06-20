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
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def get_price_change(symbol, target_date_str, target_hour):
    """
    Determines the price change for a given cryptocurrency symbol at a specific hour.
    """
    # Convert target date and hour to UTC timestamp
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    target_datetime = target_date.replace(hour=target_hour)
    eastern = pytz.timezone('US/Eastern')
    target_datetime = eastern.localize(target_datetime)
    utc_datetime = target_datetime.astimezone(pytz.utc)
    
    start_time = int(utc_datetime.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later
    
    # Fetch price data
    data = fetch_price_data(symbol, "1h", start_time, end_time)
    
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change = (close_price - open_price) / open_price * 100
        return price_change
    else:
        return None

def main():
    """
    Main function to determine if the price of BTC/USDT went up or down.
    """
    symbol = "BTCUSDT"
    target_date_str = "2025-06-17"
    target_hour = 12  # 12 PM ET
    
    price_change = get_price_change(symbol, target_date_str, target_hour)
    
    if price_change is not None:
        if price_change >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50

if __name__ == "__main__":
    main()