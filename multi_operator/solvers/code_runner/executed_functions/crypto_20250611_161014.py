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
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def get_data(symbol, start_time, end_time, proxy_url, primary_url):
    """
    Fetches data from Binance API using a proxy and falls back to the primary endpoint if necessary.
    """
    try:
        # First try the proxy endpoint
        response = requests.get(f"{proxy_url}?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Close price
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}/klines?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Close price

def resolve_market():
    """
    Resolves the market based on the close prices of XRP/USDT on Binance at specific times.
    """
    symbol = "XRPUSDT"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3"
    
    # Convert ET to UTC
    tz = pytz.timezone("US/Eastern")
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Dates and times for the candles
    start_date_str = "2025-06-10 12:00:00"
    end_date_str = "2025-06-11 12:00:00"
    
    start_date = tz.localize(datetime.strptime(start_date_str, date_format)).astimezone(pytz.utc)
    end_date = tz.localize(datetime.strptime(end_date_str, date_format)).astimezone(pytz.utc)
    
    start_time_ms = int(start_date.timestamp() * 1000)
    end_time_ms = int(end_date.timestamp() * 1000)
    
    # Fetch close prices
    close_price_start = get_data(symbol, start_time_ms, start_time_ms + 60000, proxy_url, primary_url)
    close_price_end = get_data(symbol, end_time_ms, end_time_ms + 60000, proxy_url, primary_url)
    
    # Determine resolution
    if close_price_end > close_price_start:
        return "recommendation: p2"  # Up
    elif close_price_end < close_price_start:
        return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # 50-50

if __name__ == "__main__":
    result = resolve_market()
    print(result)