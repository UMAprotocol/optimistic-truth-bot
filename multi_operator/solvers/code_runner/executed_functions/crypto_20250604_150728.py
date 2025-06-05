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

def get_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")

        # Fallback to primary endpoint
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {e}")
            raise

def resolve_market(symbol, target_date, target_hour):
    """
    Resolves the market based on the price change of the BTC/USDT pair on Binance.
    """
    tz = pytz.timezone("US/Eastern")
    target_datetime = datetime(target_date.year, target_date.month, target_date.day, target_hour, 0, 0, tzinfo=tz)
    target_datetime_utc = target_datetime.astimezone(pytz.utc)
    start_time = int(target_datetime_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    try:
        data = get_binance_data(symbol, "1h", start_time, end_time)
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            price_change = close_price - open_price
            recommendation = "p2" if price_change < 0 else "p1"
            return recommendation
    except Exception as e:
        logger.error(f"Error fetching or processing data: {e}")
        return "p3"  # Unknown or error

def main():
    """
    Main function to execute the market resolution logic.
    """
    symbol = "BTCUSDT"
    target_date = datetime(2025, 6, 4)
    target_hour = 8  # 8 AM ET

    recommendation = resolve_market(symbol, target_date, target_hour)
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()