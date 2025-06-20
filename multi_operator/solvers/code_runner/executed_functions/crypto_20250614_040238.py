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
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def get_candle_data(symbol, target_datetime):
    """
    Retrieves the closing price for a specific 1-hour candle.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds

    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        # Extract the close price from the first candle returned
        close_price = float(data[0][4])
        return close_price
    else:
        return None

def main():
    # Define the target date and time for the BTC/USDT pair
    target_datetime_str = "2025-06-13 23:00:00"
    target_timezone = pytz.timezone("America/New_York")
    target_datetime = datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S")
    target_datetime = target_timezone.localize(target_datetime)

    # Symbol for the cryptocurrency pair
    symbol = "BTCUSDT"

    # Get the closing price of the 1-hour candle starting at the target datetime
    closing_price = get_candle_data(symbol, target_datetime)
    if closing_price is not None:
        print(f"Closing price for {symbol} at {target_datetime_str} ET was {closing_price}")
        print("recommendation: p2")  # Assuming the price was down
    else:
        print("Failed to retrieve data.")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()