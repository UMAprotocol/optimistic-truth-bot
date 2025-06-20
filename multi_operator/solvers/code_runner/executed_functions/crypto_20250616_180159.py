import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance using a proxy with a fallback to the primary API.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy API.")
        return data
    except Exception as e:
        logging.warning(f"Proxy API failed: {e}. Attempting to fetch from primary API.")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary API.")
            return data
        except Exception as e:
            logging.error(f"Primary API failed: {e}.")
            raise

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the price change of the ETH/USDT pair at a specific time.
    """
    # Convert target time to UTC milliseconds
    target_time_utc = int(target_time.timestamp() * 1000)
    one_hour_ms = 3600000  # 1 hour in milliseconds

    # Fetch price data for the specified hour
    data = fetch_price_data(symbol, "1h", target_time_utc, target_time_utc + one_hour_ms)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change = close_price - open_price
        
        if price_change >= 0:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 if no data available

def main():
    """
    Main function to execute the market resolution logic.
    """
    # Define the target time for the market resolution
    target_time_str = "2025-06-16 13:00:00"
    timezone = pytz.timezone("US/Eastern")
    target_time = timezone.localize(datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S"))
    
    # Symbol for the market
    symbol = "ETHUSDT"
    
    try:
        resolution = resolve_market(symbol, target_time)
        print(f"recommendation: {resolution}")
    except Exception as e:
        logging.error(f"Error resolving market: {e}")
        print("recommendation: p3")  # Default to unknown if there's an error

if __name__ == "__main__":
    main()