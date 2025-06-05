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
        symbol (str): The symbol to fetch data for, e.g., 'BTCUSDT'.
        interval (str): The interval of the klines data, e.g., '1h'.
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    
    Returns:
        float: The closing price of the symbol at the specified time.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
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

def resolve_market(symbol, target_date_str, target_hour):
    """
    Resolves the market based on the price change of a cryptocurrency on Binance.
    
    Args:
        symbol (str): The cryptocurrency symbol, e.g., 'BTCUSDT'.
        target_date_str (str): The target date in 'YYYY-MM-DD' format.
        target_hour (int): The hour of the day in 24-hour format for the 1-hour candle.
    
    Returns:
        str: 'p1' if price went down, 'p2' if price went up, 'p3' if unknown.
    """
    # Convert target date and hour to the start and end timestamps of the 1-hour candle
    tz = pytz.timezone("America/New_York")
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    target_datetime = tz.localize(datetime(target_date.year, target_date.month, target_date.day, target_hour, 0, 0))
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds

    try:
        closing_price_start = fetch_price_data(symbol, "1h", start_time, start_time + 60000)  # Start of the hour
        closing_price_end = fetch_price_data(symbol, "1h", end_time - 60000, end_time)  # End of the hour

        if closing_price_end >= closing_price_start:
            return "p2"  # Price went up
        else:
            return "p1"  # Price went down
    except Exception as e:
        print(f"Error resolving market: {e}")
        return "p3"  # Unknown or error

def main():
    # Example usage
    result = resolve_market("BTCUSDT", "2025-05-31", 13)  # May 31, 2025, 1 PM ET
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()