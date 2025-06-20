import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

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
        print(f"Proxy failed with error: {e}, falling back to primary API.")
        # Fallback to the primary API endpoint
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
            return None

def get_candle_data(symbol, target_datetime):
    """
    Retrieves the closing price of a specific 1-hour candle for the given datetime.
    """
    # Convert datetime to milliseconds
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds
    
    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        # Extract the close price from the first candle data
        close_price = float(data[0][4])
        return close_price
    else:
        return None

def main():
    # Define the target date and time
    target_datetime_str = "2025-06-15 07:00:00"
    target_timezone = pytz.timezone("US/Eastern")
    target_datetime = datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S")
    target_datetime = target_timezone.localize(target_datetime)
    
    # Convert target datetime to UTC
    target_datetime_utc = target_datetime.astimezone(pytz.utc)
    
    # Symbol for the market
    symbol = "BTCUSDT"
    
    # Get the closing price of the 1-hour candle starting at the target datetime
    close_price_start = get_candle_data(symbol, target_datetime_utc)
    
    # Get the closing price of the previous 1-hour candle
    close_price_end = get_candle_data(symbol, target_datetime_utc + timedelta(hours=1))
    
    if close_price_start is not None and close_price_end is not None:
        # Calculate the percentage change
        percentage_change = ((close_price_end - close_price_start) / close_price_start) * 100
        
        # Determine the resolution based on the percentage change
        if percentage_change >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 if data is not available

if __name__ == "__main__":
    main()