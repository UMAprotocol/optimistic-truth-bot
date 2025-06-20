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
        # Try fetching data from the proxy endpoint first
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

def get_candle_data(symbol, target_datetime):
    """
    Retrieves the closing price of a specific 1-hour candle for the given datetime.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds
    
    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        # Extract the closing price from the first candle data
        close_price = float(data[0][4])
        return close_price
    else:
        raise ValueError("No data returned from API.")

def main():
    """
    Main function to determine if the Bitcoin price went up or down at the specified time.
    """
    # Specific date and time for the market question
    target_datetime_str = "2025-06-13 21:00:00"
    target_timezone = "US/Eastern"
    symbol = "BTCUSDT"
    
    # Convert string to datetime object in the specified timezone
    tz = pytz.timezone(target_timezone)
    target_datetime = datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S")
    target_datetime = tz.localize(target_datetime)
    
    # Convert target datetime to UTC
    target_datetime_utc = target_datetime.astimezone(pytz.utc)
    
    try:
        # Get the closing price of the 1-hour candle starting at the target datetime
        closing_price_start = get_candle_data(symbol, target_datetime_utc)
        
        # Get the closing price of the 1-hour candle one hour before the target datetime
        one_hour_before = target_datetime_utc - timedelta(hours=1)
        closing_price_before = get_candle_data(symbol, one_hour_before)
        
        # Determine if the price went up or down
        if closing_price_start >= closing_price_before:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        print(f"Error fetching data: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    main()