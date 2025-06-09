import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

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
        print(f"Proxy API failed: {e}, falling back to primary API")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data[0][4])  # Closing price
        except Exception as e:
            print(f"Primary API failed: {e}")
            raise

def resolve_market(symbol, target_date_str, target_hour):
    """
    Resolves the market based on the price change of a cryptocurrency on Binance.
    
    Args:
        symbol (str): The cryptocurrency symbol.
        target_date_str (str): The target date in 'YYYY-MM-DD' format.
        target_hour (int): The hour in ET for which the price change is calculated.
    
    Returns:
        str: The resolution of the market ('p1' for down, 'p2' for up).
    """
    # Convert target time to UTC
    et_timezone = pytz.timezone("US/Eastern")
    target_datetime = datetime.strptime(target_date_str, "%Y-%m-%d")
    target_datetime = et_timezone.localize(datetime(target_datetime.year, target_datetime.month, target_datetime.day, target_hour, 0, 0))
    target_datetime_utc = target_datetime.astimezone(pytz.utc)
    
    # Calculate start and end times in milliseconds
    start_time_ms = int(target_datetime_utc.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later
    
    # Fetch closing prices at the start and end of the target hour
    start_price = fetch_price_data(symbol, "1h", start_time_ms, start_time_ms + 60000)  # Start of the hour
    end_price = fetch_price_data(symbol, "1h", end_time_ms - 60000, end_time_ms)  # End of the hour
    
    # Determine if the price went up or down
    if end_price >= start_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    """
    Main function to execute the market resolution.
    """
    try:
        resolution = resolve_market("BTCUSDT", "2025-06-06", 23)  # June 6, 2025, 11 PM ET
        print(f"recommendation: {resolution}")
    except Exception as e:
        print(f"Failed to resolve market: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()