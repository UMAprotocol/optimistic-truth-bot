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
        symbol (str): The symbol to fetch data for (e.g., 'BTCUSDT').
        interval (str): The interval of the klines data (e.g., '1h').
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

def resolve_market(symbol, target_date_str, target_hour):
    """
    Resolves the market based on the price change of a cryptocurrency on Binance.
    
    Args:
        symbol (str): The cryptocurrency symbol (e.g., 'BTCUSDT').
        target_date_str (str): The target date in 'YYYY-MM-DD' format.
        target_hour (int): The hour of the day in 24-hour format for the target time.
    
    Returns:
        str: Market resolution recommendation.
    """
    # Convert target time to UTC timestamp
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    target_time = target_date.replace(hour=target_hour, minute=0, second=0, microsecond=0)
    target_time = pytz.timezone("US/Eastern").localize(target_time).astimezone(pytz.utc)
    
    start_time_ms = int(target_time.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later
    
    # Fetch closing prices at the start and end of the target hour
    start_price = fetch_price_data(symbol, "1h", start_time_ms, start_time_ms + 60000)  # 1 minute after start
    end_price = fetch_price_data(symbol, "1h", end_time_ms - 60000, end_time_ms)  # 1 minute before end
    
    # Determine market resolution
    if end_price >= start_price:
        return "recommendation: p2"  # Up
    else:
        return "recommendation: p1"  # Down

def main():
    """
    Main function to execute the market resolution logic.
    """
    try:
        resolution = resolve_market("BTCUSDT", "2025-05-29", 14)  # May 29, 2025, 2 PM ET
        print(resolution)
    except Exception as e:
        print(f"An error occurred: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()