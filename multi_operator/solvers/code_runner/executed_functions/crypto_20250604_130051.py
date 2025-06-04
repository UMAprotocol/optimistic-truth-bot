import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching data using the proxy URL first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
        else:
            raise ValueError("No data returned from proxy.")
    except Exception as e:
        print(f"Proxy failed with error: {e}. Trying primary API endpoint.")
        try:
            # Fallback to the primary API endpoint if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Primary API also failed with error: {e}.")
            return None

def get_candle_data(symbol, target_datetime):
    """
    Retrieves the closing price of a specific 1-hour candle for the given datetime.
    """
    # Convert datetime to the correct format for the API call
    start_time = int(target_datetime.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # Add one hour in milliseconds

    # Fetch data
    data = fetch_binance_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        close_price = float(data[0][4])  # Closing price is the fifth element in the list
        return close_price
    else:
        return None

def main():
    # Define the target date and time
    target_date_str = "2025-06-04"
    target_time_str = "05:00:00"
    timezone_str = "US/Eastern"

    # Convert string to datetime object in the specified timezone
    timezone = pytz.timezone(timezone_str)
    target_datetime = timezone.localize(datetime.strptime(f"{target_date_str} {target_time_str}", "%Y-%m-%d %H:%M:%S"))

    # Symbol for which the data is to be fetched
    symbol = "BTCUSDT"

    # Get the closing price of the target candle
    closing_price = get_candle_data(symbol, target_datetime)
    if closing_price is not None:
        print(f"The closing price of {symbol} at {target_datetime} was {closing_price}")
    else:
        print("Failed to retrieve the closing price.")

if __name__ == "__main__":
    main()