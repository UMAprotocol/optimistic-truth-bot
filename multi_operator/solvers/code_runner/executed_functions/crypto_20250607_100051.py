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
    
    Args:
        symbol (str): The symbol to fetch data for.
        interval (str): The interval of the klines data.
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    
    Returns:
        float: The closing price of the symbol at the specified time.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy API first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Closing price
    except Exception as e:
        print(f"Proxy API failed, error: {e}. Falling back to primary API.")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data[0][4])  # Closing price
        except Exception as e:
            print(f"Primary API also failed, error: {e}.")
            raise

def convert_to_utc(year, month, day, hour, minute, timezone_str):
    """
    Converts local time to UTC timestamp in milliseconds.
    
    Args:
        year (int): Year of the date.
        month (int): Month of the date.
        day (int): Day of the date.
        hour (int): Hour of the day.
        minute (int): Minute of the hour.
        timezone_str (str): Timezone string.
    
    Returns:
        int: UTC timestamp in milliseconds.
    """
    local_tz = pytz.timezone(timezone_str)
    local_time = local_tz.localize(datetime(year, month, day, hour, minute))
    utc_time = local_time.astimezone(pytz.utc)
    return int(utc_time.timestamp() * 1000)

def main():
    # Specific date and time for the query
    year, month, day = 2025, 6, 7
    hour, minute = 5, 0  # 5 AM ET
    timezone_str = "US/Eastern"
    
    # Convert local time to UTC timestamp in milliseconds
    start_time = convert_to_utc(year, month, day, hour, minute, timezone_str)
    end_time = start_time + 3600000  # Plus one hour
    
    # Symbol for the cryptocurrency
    symbol = "BTCUSDT"
    
    try:
        # Fetch the closing price for the specified time
        closing_price = fetch_price_data(symbol, "1h", start_time, end_time)
        print(f"Closing price for {symbol} at {datetime.utcfromtimestamp(start_time / 1000)} UTC: {closing_price}")
    except Exception as e:
        print(f"Failed to fetch data: {e}")

if __name__ == "__main__":
    main()