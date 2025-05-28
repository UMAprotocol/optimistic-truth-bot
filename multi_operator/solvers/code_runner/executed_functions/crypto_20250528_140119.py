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
        logging.warning(f"Proxy API failed: {e}. Attempting primary API.")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary API.")
            return data
        except Exception as e:
            logging.error(f"Both API requests failed: {e}")
            raise

def get_candle_data(symbol, date_str, hour):
    """
    Retrieves the closing price for a specific hour candle on a given date for the specified symbol.
    """
    # Convert date and hour to the correct timestamp
    date = datetime.strptime(date_str, "%Y-%m-%d")
    date = date.replace(hour=hour, minute=0, second=0, microsecond=0)
    tz = pytz.timezone("America/New_York")
    date = tz.localize(date)
    start_time = int(date.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds

    # Fetch the candle data
    data = fetch_data_from_binance(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        close_price = float(data[0][4])
        open_price = float(data[0][1])
        return close_price, open_price
    else:
        logging.error("No data available for the specified time and symbol.")
        return None, None

def resolve_market():
    """
    Resolves the market based on the price movement of BTC/USDT on Binance for the specified candle.
    """
    symbol = "BTCUSDT"
    date_str = "2025-05-28"
    hour = 9  # 9 AM ET

    try:
        close_price, open_price = get_candle_data(symbol, date_str, hour)
        if close_price is not None and open_price is not None:
            if close_price >= open_price:
                logging.info("Market resolves to Up.")
                print("recommendation: p2")  # Up
            else:
                logging.info("Market resolves to Down.")
                print("recommendation: p1")  # Down
        else:
            logging.info("Data is inconclusive.")
            print("recommendation: p3")  # Unknown/50-50
    except Exception as e:
        logging.error(f"Failed to resolve market due to an error: {e}")
        print("recommendation: p3")  # Unknown/50-50

if __name__ == "__main__":
    resolve_market()