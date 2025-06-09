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

def get_data(symbol, interval, start_time):
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
        "endTime": start_time + 3600000  # 1 hour later
    }

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(primary_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market(symbol, target_date, target_hour):
    """
    Resolves the market based on the price change of the specified symbol at the given date and hour.
    """
    tz = pytz.timezone("US/Eastern")
    dt = datetime.strptime(target_date, "%Y-%m-%d")
    dt = tz.localize(datetime(dt.year, dt.month, dt.day, target_hour, 0, 0))
    start_time = int(dt.timestamp() * 1000)  # Convert to milliseconds

    data = get_data(symbol, "1h", start_time)
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        change = (close_price - open_price) / open_price * 100

        if change >= 0:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50

def main():
    """
    Main function to handle the resolution of the Bitcoin Up or Down market.
    """
    symbol = "BTCUSDT"
    target_date = "2025-06-08"
    target_hour = 8  # 8 AM ET

    result = resolve_market(symbol, target_date, target_hour)
    print(result)

if __name__ == "__main__":
    main()