import requests
import logging
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

def fetch_eth_high_price(start_date, end_date, target_price):
    """
    Fetches the highest price of Ethereum (ETHUSDT) from Binance within a specified date range
    and checks if it reached or exceeded the target price.

    Args:
        start_date (str): Start date in 'YYYY-MM-DD' format.
        end_date (str): End date in 'YYYY-MM-DD' format.
        target_price (float): Target price to check.

    Returns:
        str: 'p1' if the price never reached the target, 'p2' if it did.
    """
    symbol = "ETHUSDT"
    interval = "1m"
    base_url = "https://api.binance.com/api/v3/klines"
    
    # Convert dates to milliseconds
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # Include the end date fully
    start_ts = int(start_dt.replace(tzinfo=timezone.utc).timestamp() * 1000)
    end_ts = int(end_dt.replace(tzinfo=timezone.utc).timestamp() * 1000)

    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_ts,
        "endTime": end_ts,
        "limit": 1000  # Maximum limit
    }

    try:
        while True:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                break

            for candle in data:
                high_price = float(candle[2])  # High price is the third element
                if high_price >= target_price:
                    return "p2"  # Yes, price reached or exceeded the target

            # Update startTime for the next batch
            last_candle_time = int(data[-1][6])  # Closing time of the last candle
            params["startTime"] = last_candle_time + 1

    except requests.RequestException as e:
        logger.error(f"Error fetching data from Binance: {e}")
        return "p3"  # Unknown due to error

    return "p1"  # No, price never reached the target

def main():
    """
    Main function to check if Ethereum reached $2800 in June 2025.
    """
    start_date = "2025-06-01"
    end_date = "2025-06-30"
    target_price = 2800.0

    result = fetch_eth_high_price(start_date, end_date, target_price)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()