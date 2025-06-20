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
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fallback to the primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def get_eth_price_change(symbol, target_datetime):
    """
    Calculates the percentage change for the ETH/USDT pair for the specified 1-hour candle.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds
    
    # Fetch price data
    data = fetch_price_data(symbol, "1h", start_time, end_time)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        change_percent = ((close_price - open_price) / open_price) * 100
        return change_percent
    else:
        raise ValueError("No data available for the specified time.")

def main():
    """
    Main function to determine if the ETH price went up or down at the specified time.
    """
    # Define the target date and time
    target_datetime = datetime(2025, 6, 15, 3, 0, tzinfo=pytz.timezone("US/Eastern"))
    
    try:
        # Get the percentage change for ETH/USDT
        change_percent = get_eth_price_change("ETHUSDT", target_datetime)
        
        # Determine the resolution based on the change percentage
        if change_percent >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        print(f"Error: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    main()