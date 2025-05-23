import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables
load_dotenv()

# API keys
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API = "https://api.binance.com/api/v3/klines"
PROXY_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_price(symbol, date_str, timezone_str="US/Eastern"):
    """
    Fetch the closing price of a cryptocurrency from Binance at a specific time.
    """
    # Convert date string to the correct timestamp
    tz = pytz.timezone(timezone_str)
    naive_dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    local_dt = tz.localize(naive_dt)
    utc_dt = local_dt.astimezone(pytz.utc)
    timestamp = int(utc_dt.timestamp() * 1000)  # Convert to milliseconds

    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": timestamp,
        "endTime": timestamp + 60000  # 1 minute later
    }

    try:
        # Try fetching from the proxy API first
        response = requests.get(PROXY_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price
    except Exception as e:
        logging.warning(f"Proxy API failed, trying primary API: {e}")
        # Fallback to the primary API if proxy fails
        try:
            response = requests.get(PRIMARY_API, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            close_price = float(data[0][4])
            return close_price
        except Exception as e:
            logging.error(f"Both API requests failed: {e}")
            raise

def main():
    """
    Main function to determine if the price of Ethereum went up or down between two specific times.
    """
    symbol = "ETHUSDT"
    date1 = "2025-04-19 12:00"
    date2 = "2025-04-20 12:00"

    try:
        price1 = fetch_price(symbol, date1)
        price2 = fetch_price(symbol, date2)
        logging.info(f"Price on {date1}: {price1}")
        logging.info(f"Price on {date2}: {price2}")

        if price1 < price2:
            print("recommendation: p2")  # Up
        elif price1 > price2:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    except Exception as e:
        logging.error(f"Error in fetching prices: {e}")
        print("recommendation: p4")  # Unknown or error

if __name__ == "__main__":
    main()