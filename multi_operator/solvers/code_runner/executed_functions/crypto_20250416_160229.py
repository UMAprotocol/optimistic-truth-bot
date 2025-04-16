import requests
import logging
from datetime import datetime
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def get_close_price_at_specific_time(symbol, date_str, hour=12, minute=0, timezone_str="US/Eastern"):
    """
    Fetches the 1-minute candle close price for a cryptocurrency pair on Binance
    at a specific time on a given date.
    """
    logger.info(f"Fetching close price for {symbol} on {date_str} at {hour}:{minute} {timezone_str}")
    
    # Convert the target time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    target_time_local = tz.localize(datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S"))
    target_time_utc = target_time_local.astimezone(pytz.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)

    # Binance API endpoint
    api_url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time_ms,
        "endTime": start_time_ms + 60000  # 1 minute later
    }

    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price
    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        return None

def main():
    """
    Main function to determine if the price of Ethereum on Binance went up or down
    between two specific times.
    """
    symbol = "ETHUSDT"
    date1 = "2025-04-15"
    date2 = "2025-04-16"
    hour = 12
    minute = 0
    timezone_str = "US/Eastern"

    price1 = get_close_price_at_specific_time(symbol, date1, hour, minute, timezone_str)
    price2 = get_close_price_at_specific_time(symbol, date2, hour, minute, timezone_str)

    if price1 is None or price2 is None:
        print("recommendation: p4")
        return

    if price2 > price1:
        print("recommendation: p2")
    elif price2 < price1:
        print("recommendation: p1")
    else:
        print("recommendation: p3")

if __name__ == "__main__":
    main()