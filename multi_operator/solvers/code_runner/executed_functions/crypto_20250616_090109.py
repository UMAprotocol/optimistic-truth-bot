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

def fetch_price_data(symbol, interval, start_time):
    """
    Fetches price data from Binance using either the proxy or primary endpoint.
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
        # Try fetching data from the proxy endpoint
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {e}")
            raise

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the price change of the symbol at the specified target time.
    """
    try:
        # Convert target time to UTC timestamp
        target_time_utc = int(target_time.replace(tzinfo=timezone.utc).timestamp() * 1000)
        data = fetch_price_data(symbol, "1h", target_time_utc)
        
        if data:
            open_price = float(data[1])
            close_price = float(data[4])
            change_percentage = ((close_price - open_price) / open_price) * 100
            
            if change_percentage >= 0:
                return "recommendation: p2"  # Up
            else:
                return "recommendation: p1"  # Down
    except Exception as e:
        logger.error(f"Error resolving market: {e}")
        return "recommendation: p3"  # Unknown/50-50

def main():
    """
    Main function to handle the resolution of the Ethereum market.
    """
    symbol = "ETHUSDT"
    target_time = datetime(2025, 6, 16, 4, 0, tzinfo=pytz.timezone("US/Eastern"))
    
    result = resolve_market(symbol, target_time)
    print(result)

if __name__ == "__main__":
    main()