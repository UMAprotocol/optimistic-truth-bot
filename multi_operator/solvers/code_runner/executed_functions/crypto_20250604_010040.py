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
        try:
            response = requests.get(f"{primary_url}?symbol={symbol}&interval=1h&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {str(e)}")
            raise

def resolve_market():
    # Define the specific date and time for the event
    event_date = "2025-06-03"
    event_time = "20:00:00"
    timezone_str = "US/Eastern"
    
    # Convert the event time to UTC
    tz = pytz.timezone(timezone_str)
    naive_dt = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M:%S")
    local_dt = tz.localize(naive_dt)
    utc_dt = local_dt.astimezone(pytz.utc)
    
    # Calculate start and end timestamps in milliseconds
    start_time = int(utc_dt.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later
    
    # Fetch the data for the BTC/USDT pair
    try:
        data = get_data("BTCUSDT", start_time, end_time)
        open_price = float(data[1])
        close_price = float(data[4])
        
        # Determine if the price went up or down
        if close_price >= open_price:
            logger.info("Market resolves to Up.")
            print("recommendation: p2")  # p2 corresponds to Up
        else:
            logger.info("Market resolves to Down.")
            print("recommendation: p1")  # p1 corresponds to Down
    except Exception as e:
        logger.error(f"Failed to resolve market due to an error: {e}")
        print("recommendation: p3")  # p3 corresponds to unknown/50-50

if __name__ == "__main__":
    resolve_market()