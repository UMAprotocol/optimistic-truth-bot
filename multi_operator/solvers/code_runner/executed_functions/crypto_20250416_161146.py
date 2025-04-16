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
handler.setLevel(logging.DEBUG)
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
    target_time_local = tz.localize(datetime.strptime(f"{date_str} {hour:02d}:{minute:02d}:00", "%Y-%m-%d %H:%M:%S"))
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

    response = requests.get(api_url, params=params)
    response.raise_for_status()
    data = response.json()

    if data and len(data) > 0:
        close_price = float(data[0][4])
        return close_price
    else:
        raise ValueError("No data returned from API.")

def main():
    try:
        # Fetch prices for the specified dates and times
        price_apr_15 = get_close_price_at_specific_time("ETHUSDT", "2025-04-15", 12, 0, "US/Eastern")
        price_apr_16 = get_close_price_at_specific_time("ETHUSDT", "2025-04-16", 12, 0, "US/Eastern")

        # Determine the market resolution
        if price_apr_16 > price_apr_15:
            recommendation = "p2"  # Up
        elif price_apr_16 < price_apr_15:
            recommendation = "p1"  # Down
        else:
            recommendation = "p3"  # 50-50

        print(f"recommendation: {recommendation}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()