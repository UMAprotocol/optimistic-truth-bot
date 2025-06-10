import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables
load_dotenv()

# API keys
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API URLs
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
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
        logging.info("Data fetched successfully from proxy API.")
        return data
    except Exception as e:
        logging.warning(f"Proxy API failed: {e}. Falling back to primary API.")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary API.")
            return data
        except Exception as e:
            logging.error(f"Primary API also failed: {e}.")
            raise

def resolve_market(symbol, target_date_str, target_hour):
    """
    Resolves the market based on the price change of the cryptocurrency.
    """
    # Convert target date and hour to UTC timestamp
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    target_time = target_date.replace(hour=target_hour)
    eastern = pytz.timezone('US/Eastern')
    target_time = eastern.localize(target_time)
    utc_time = target_time.astimezone(pytz.utc)
    
    start_time = int(utc_time.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later
    
    # Fetch price data
    try:
        data = fetch_price_data(symbol, "1h", start_time, end_time)
        if data and len(data) > 0:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            price_change = (close_price - open_price) / open_price * 100
            
            if price_change >= 0:
                logging.info(f"Market resolves to Up. Price change: {price_change}%")
                return "recommendation: p2"  # Up
            else:
                logging.info(f"Market resolves to Down. Price change: {price_change}%")
                return "recommendation: p1"  # Down
        else:
            logging.error("No data available to resolve the market.")
            return "recommendation: p3"  # Unknown/50-50
    except Exception as e:
        logging.error(f"Failed to fetch or process data: {e}")
        return "recommendation: p3"  # Unknown/50-50

def main():
    # Example usage
    symbol = "BTCUSDT"
    target_date_str = "2025-06-04"
    target_hour = 10  # 10 AM ET
    result = resolve_market(symbol, target_date_str, target_hour)
    print(result)

if __name__ == "__main__":
    main()