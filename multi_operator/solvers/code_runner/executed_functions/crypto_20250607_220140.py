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

# API endpoints
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
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logging.warning(f"Proxy failed with error: {e}. Trying primary API.")
        # Fallback to the primary API endpoint
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary API.")
            return data
        except Exception as e:
            logging.error(f"Primary API failed with error: {e}.")
            raise

def resolve_market(symbol, target_date, target_hour):
    """
    Resolves the market based on the price change of the symbol at the specified hour on target_date.
    """
    # Convert target date and hour to the correct timestamp
    tz = pytz.timezone("America/New_York")
    dt = datetime.strptime(target_date, "%Y-%m-%d")
    dt = tz.localize(datetime(dt.year, dt.month, dt.day, target_hour, 0, 0))
    start_timestamp = int(dt.timestamp() * 1000)
    end_timestamp = start_timestamp + 3600000  # 1 hour later

    # Fetch price data
    data = fetch_price_data(symbol, "1h", start_timestamp, end_timestamp)

    if not data or len(data) == 0:
        logging.error("No data available for the specified time.")
        return "recommendation: p4"

    # Calculate the percentage change
    open_price = float(data[0][1])
    close_price = float(data[0][4])
    change_percentage = ((close_price - open_price) / open_price) * 100

    # Determine the resolution based on the change
    if change_percentage >= 0:
        return "recommendation: p2"  # Up
    else:
        return "recommendation: p1"  # Down

def main():
    """
    Main function to execute the market resolution logic.
    """
    symbol = "BTCUSDT"
    target_date = "2025-06-07"
    target_hour = 17  # 5 PM ET
    result = resolve_market(symbol, target_date, target_hour)
    print(result)

if __name__ == "__main__":
    main()