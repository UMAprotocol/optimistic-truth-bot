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
        return response.json()
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}?symbol={symbol}&interval=1h&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market():
    # Define the specific date and time for the event
    event_date = datetime(2025, 6, 6, 13, 0, 0)  # June 6, 2025, 1 PM ET
    tz = pytz.timezone("US/Eastern")
    event_date_utc = tz.localize(event_date).astimezone(pytz.utc)
    
    start_time = int(event_date_utc.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # Plus one hour
    
    data = get_data("BTCUSDT", start_time, end_time)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        change_percentage = ((close_price - open_price) / open_price) * 100
        
        if change_percentage >= 0:
            recommendation = "p2"  # Up
        else:
            recommendation = "p1"  # Down
    else:
        recommendation = "p3"  # Unknown/50-50 if no data available
    
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    resolve_market()