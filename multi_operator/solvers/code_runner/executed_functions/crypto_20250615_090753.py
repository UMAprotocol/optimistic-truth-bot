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

def get_binance_price(symbol, interval, start_time):
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
        # Try proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0][4]  # Close price of the candle
    except Exception as e:
        logger.error(f"Proxy failed, error: {e}. Trying primary endpoint.")
        try:
            # Fallback to primary endpoint
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0][4]  # Close price of the candle
        except Exception as e:
            logger.error(f"Primary endpoint also failed, error: {e}")
            raise

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the price change of the cryptocurrency.
    """
    try:
        # Convert target time to UTC milliseconds
        target_datetime = datetime.strptime(target_time, "%Y-%m-%d %H:%M %Z")
        target_timestamp = int(target_datetime.replace(tzinfo=timezone.utc).timestamp() * 1000)
        
        # Get the closing price at the start of the target hour
        start_price = float(get_binance_price(symbol, "1h", target_timestamp))
        
        # Get the closing price at the end of the target hour
        end_price = float(get_binance_price(symbol, "1h", target_timestamp + 3600000))
        
        # Determine if the price went up or down
        if end_price >= start_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    except Exception as e:
        logger.error(f"Error resolving market: {e}")
        return "recommendation: p3"  # Unknown/50-50 if error occurs

def main():
    """
    Main function to execute the market resolution.
    """
    # Example date and time for the market resolution
    target_time = "2025-06-15 04:00 EDT"
    symbol = "BTCUSDT"
    
    result = resolve_market(symbol, target_time)
    print(result)

if __name__ == "__main__":
    main()