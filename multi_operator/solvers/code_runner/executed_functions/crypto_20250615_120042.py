import requests
import logging
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_binance_data(symbol, interval, start_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    
    Args:
        symbol (str): The symbol to fetch data for, e.g., 'BTCUSDT'
        interval (str): The interval of the data, e.g., '1h'
        start_time (int): The start time in milliseconds since the epoch
    
    Returns:
        float: The percentage change of the price if data is available, otherwise None
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"
    
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later
    }
    
    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return ((close_price - open_price) / open_price) * 100
    except Exception as e:
        logging.warning(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                open_price = float(data[0][1])
                close_price = float(data[0][4])
                return ((close_price - open_price) / open_price) * 100
        except Exception as e:
            logging.error(f"Primary endpoint also failed: {e}")
            return None

def resolve_market():
    """
    Resolves the market based on the Bitcoin price change on Binance.
    """
    # Define the specific time and date for the market resolution
    target_datetime = datetime(2025, 6, 15, 7, 0, tzinfo=pytz.timezone('US/Eastern'))
    target_timestamp = int(target_datetime.timestamp() * 1000)  # Convert to milliseconds
    
    # Get the percentage change for BTC/USDT
    change_percentage = get_binance_data("BTCUSDT", "1h", target_timestamp)
    
    if change_percentage is None:
        recommendation = "p3"  # Unknown/50-50 if no data could be fetched
    elif change_percentage >= 0:
        recommendation = "p2"  # Up
    else:
        recommendation = "p1"  # Down
    
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    resolve_market()