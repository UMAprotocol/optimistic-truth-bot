import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz
import logging

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_binance_data(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Maximum allowed by Binance
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data using the proxy endpoint
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy endpoint.")
        return data
    except Exception as e:
        logging.warning(f"Proxy endpoint failed: {e}. Falling back to primary endpoint.")
        # Fallback to the primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logging.error(f"Both proxy and primary endpoints failed: {e}")
            return None

def check_bitcoin_price_threshold(start_date, end_date, threshold):
    """
    Checks if Bitcoin price reached a certain threshold within a given date range.
    """
    # Convert dates to timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))
    
    start_timestamp = int(start_dt.timestamp() * 1000)
    end_timestamp = int(end_dt.timestamp() * 1000)
    
    # Fetch data from Binance
    data = fetch_binance_data("BTCUSDT", start_timestamp, end_timestamp)
    
    if data:
        # Check if any candle high price meets or exceeds the threshold
        for candle in data:
            high_price = float(candle[2])  # High price is the third element in each candle
            if high_price >= threshold:
                logging.info(f"Bitcoin reached ${threshold} on {datetime.fromtimestamp(candle[0] / 1000, tz).strftime('%Y-%m-%d %H:%M:%S')}")
                return True
    else:
        logging.error("Failed to fetch or process data.")
    
    return False

def main():
    """
    Main function to determine if Bitcoin reached $150k in May 2025.
    """
    if check_bitcoin_price_threshold("2025-05-01", "2025-05-31", 150000):
        print("recommendation: p2")  # Yes, Bitcoin reached $150k
    else:
        print("recommendation: p1")  # No, Bitcoin did not reach $150k

if __name__ == "__main__":
    main()