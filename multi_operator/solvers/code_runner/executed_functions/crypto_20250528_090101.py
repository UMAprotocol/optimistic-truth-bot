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

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

def get_data(symbol, start_time, end_time):
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"
    
    try:
        # First try the proxy endpoint
        response = requests.get(f"{proxy_url}?symbol={symbol}&interval=1h&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}?symbol={symbol}&interval=1h&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]

def resolve_market():
    # Define the specific date and time for the event
    event_date = "2025-05-28"
    event_time = "04:00:00"
    event_timezone = "US/Eastern"
    
    # Convert event time to UTC for API request
    tz = pytz.timezone(event_timezone)
    naive_datetime = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M:%S")
    local_datetime = tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    
    start_time = int(utc_datetime.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later in milliseconds
    
    # Fetch data for the specific candle
    symbol = "BTCUSDT"
    candle_data = get_data(symbol, start_time, end_time)
    
    if candle_data:
        open_price = float(candle_data[1])
        close_price = float(candle_data[4])
        
        # Determine if the market should resolve to "Up" or "Down"
        if close_price >= open_price:
            logger.info("Market resolves to Up.")
            print("recommendation: p2")  # p2 corresponds to "Up"
        else:
            logger.info("Market resolves to Down.")
            print("recommendation: p1")  # p1 corresponds to "Down"
    else:
        logger.error("No data available to resolve the market.")
        print("recommendation: p4")  # p4 corresponds to unknown/50-50

if __name__ == "__main__":
    resolve_market()