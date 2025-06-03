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
    Main function to determine if the Bitcoin price went up or down.
    """
    target_date_str = "2025-06-02"
    target_hour = 23  # 11 PM ET
    symbol = "BTCUSDT"
    
    # Convert target time to UTC
    et_timezone = pytz.timezone("US/Eastern")
    target_datetime = et_timezone.localize(datetime.strptime(target_date_str, "%Y-%m-%d"))
    target_datetime = target_datetime.replace(hour=target_hour)
    
    try:
        # Get the closing price of the 1-hour candle starting at 11 PM ET
        closing_price_start = get_candle_data(symbol, target_datetime)
        
        # Get the closing price of the previous 1-hour candle
        previous_candle_datetime = target_datetime - timedelta(hours=1)
        closing_price_previous = get_candle_data(symbol, previous_candle_datetime)
        
        # Determine if the price went up or down
        if closing_price_start >= closing_price_previous:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        print(f"Error: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    main()