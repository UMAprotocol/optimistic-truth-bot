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
        response = requests.get(f"{primary_url}?symbol={symbol}&interval=1h&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]

def resolve_market():
    # Define the specific date and time for the event
    event_date = "2025-05-30"
    event_time = "14:00:00"
    symbol = "BTCUSDT"
    
    # Convert local time to UTC timestamp
    tz = pytz.timezone("US/Eastern")
    dt = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M:%S")
    dt = tz.localize(dt)
    dt_utc = dt.astimezone(pytz.utc)
    start_time = int(dt_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds
    
    # Fetch data
    data = get_data(symbol, start_time, end_time)
    if data:
        open_price = float(data[1])
        close_price = float(data[4])
        
        # Determine if the price went up or down
        if close_price >= open_price:
            logger.info("Market resolves to Up.")
            return "recommendation: p2"  # Up
        else:
            logger.info("Market resolves to Down.")
            return "recommendation: p1"  # Down
    else:
        logger.error("No data available to resolve the market.")
        return "recommendation: p4"  # Unknown

if __name__ == "__main__":
    result = resolve_market()
    print(result)