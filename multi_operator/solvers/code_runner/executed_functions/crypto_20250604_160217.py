import requests
import logging
from datetime import datetime
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_binance_price(symbol, target_time):
    """
    Fetches the closing price of a cryptocurrency at a specific time from Binance.

    Args:
        symbol (str): The symbol of the cryptocurrency pair (e.g., 'BTCUSDT').
        target_time (datetime): The target datetime object in UTC.

    Returns:
        float: The closing price of the cryptocurrency.
    """
    # Convert datetime to milliseconds since epoch
    timestamp = int(target_time.timestamp() * 1000)

    # URLs for Binance API
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    # Parameters for the API request
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": timestamp,
        "endTime": timestamp + 60000  # 1 minute later
    }

    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            close_price = float(data[0][4])
            return close_price
    except Exception as e:
        logging.warning(f"Proxy endpoint failed: {e}, falling back to primary endpoint")

        # Fallback to the primary endpoint if proxy fails
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                close_price = float(data[0][4])
                return close_price
        except Exception as e:
            logging.error(f"Primary endpoint also failed: {e}")
            raise

def main():
    # Define the target date and time
    target_date_str = "2025-05-16"
    target_time_str = "12:00"
    timezone_str = "US/Eastern"

    # Convert target time to UTC
    tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(f"{target_date_str} {target_time_str}", "%Y-%m-%d %H:%M")
    local_datetime = tz.localize(naive_datetime)
    target_time_utc = local_datetime.astimezone(pytz.utc)

    # Symbol for the cryptocurrency
    symbol = "BTCUSDT"

    try:
        # Get the closing price from Binance
        close_price = get_binance_price(symbol, target_time_utc)
        logging.info(f"Close price for {symbol} at {target_date_str} {target_time_str} {timezone_str} is {close_price}")

        # Determine the resolution based on the close price
        if close_price >= 104000.01:
            print("recommendation: p2")  # Yes
        else:
            print("recommendation: p1")  # No
    except Exception as e:
        logging.error(f"Failed to retrieve or process data: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    main()