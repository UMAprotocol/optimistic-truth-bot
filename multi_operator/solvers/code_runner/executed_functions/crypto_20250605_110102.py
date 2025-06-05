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

def fetch_data_from_binance(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary request fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
    }
    
    try:
        # Try fetching data from the proxy API first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy API.")
        return data
    except Exception as e:
        logging.error(f"Proxy API failed: {e}. Attempting primary API.")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary API.")
            return data
        except Exception as e:
            logging.error(f"Primary API failed: {e}.")
            raise

def get_price_change(symbol, target_date, target_hour):
    """
    Determines if the price of a cryptocurrency has gone up or down at a specific hour.
    """
    # Convert target time to UTC timestamp
    tz = pytz.timezone("US/Eastern")
    target_datetime = datetime.strptime(f"{target_date} {target_hour}:00:00", "%Y-%m-%d %H:%M:%S")
    target_datetime = tz.localize(target_datetime)
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds

    # Fetch data
    data = fetch_data_from_binance(symbol, "1h", start_time, end_time)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change = close_price - open_price
        return "p2" if price_change < 0 else "p1"
    else:
        return "p3"

def main():
    """
    Main function to determine if the price of BTC/USDT has gone up or down.
    """
    try:
        result = get_price_change("BTCUSDT", "2025-06-05", "06")
        print(f"recommendation: {result}")
    except Exception as e:
        print("recommendation: p3")
        logging.error(f"Failed to determine price change: {e}")

if __name__ == "__main__":
    main()