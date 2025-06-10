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

def get_binance_price(symbol, start_time):
    """
    Fetches the closing price of a cryptocurrency from Binance for a specific 1-hour candle.
    
    Args:
        symbol (str): The symbol to fetch, e.g., 'BTCUSDT'
        start_time (datetime): The start time of the 1-hour candle in UTC
    
    Returns:
        float: The closing price of the candle
    """
    # Convert datetime to milliseconds since epoch
    start_time_ms = int(start_time.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later

    # URLs setup
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    # First try the proxy endpoint
    try:
        response = requests.get(
            proxy_url,
            params={
                "symbol": symbol,
                "interval": "1h",
                "limit": 1,
                "startTime": start_time_ms,
                "endTime": end_time_ms
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Closing price
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")

    # Fall back to primary endpoint if proxy fails
    try:
        response = requests.get(
            primary_url,
            params={
                "symbol": symbol,
                "interval": "1h",
                "limit": 1,
                "startTime": start_time_ms,
                "endTime": end_time_ms
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Closing price
    except Exception as e:
        logger.error(f"Primary endpoint also failed: {str(e)}")
        raise

def main():
    """
    Main function to determine if the Bitcoin price went up or down for the specified candle.
    """
    # Define the specific date and time for the candle
    et_timezone = pytz.timezone("US/Eastern")
    specific_date = et_timezone.localize(datetime(2025, 5, 29, 18, 0, 0))  # May 29, 2025, 6 PM ET
    specific_date_utc = specific_date.astimezone(pytz.utc)

    # Symbol for the market
    symbol = "BTCUSDT"

    try:
        closing_price_start = get_binance_price(symbol, specific_date_utc)
        closing_price_end = get_binance_price(symbol, specific_date_utc + timedelta(hours=1))

        # Determine if the price went up or down
        if closing_price_end >= closing_price_start:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        logger.error(f"Failed to fetch prices: {e}")
        print("recommendation: p3")  # Unknown/50-50 if error occurs

if __name__ == "__main__":
    main()