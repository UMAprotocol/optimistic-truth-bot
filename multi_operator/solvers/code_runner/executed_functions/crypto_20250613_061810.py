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

def get_eth_price_at_specific_time(date_str, hour=1, minute=0, timezone_str="US/Eastern"):
    """
    Fetches the 1-hour candle close price for ETH/USDT on Binance at a specific time on a given date.
    """
    logger.info(f"Fetching ETH/USDT price for {date_str} at {hour}:{minute} {timezone_str}")
    
    # Convert the target time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    time_str = f"{hour:02d}:{minute:02d}:00"
    target_time_local = tz.localize(
        datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    )
    target_time_utc = target_time_local.astimezone(timezone.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)
    
    # Binance API endpoint
    api_url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "ETHUSDT",
        "interval": "1h",
        "limit": 1,
        "startTime": start_time_ms,
        "endTime": start_time_ms + 3600000  # plus 1 hour
    }

    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            price_change = ((close_price - open_price) / open_price) * 100
            logger.info(f"Open price: {open_price}, Close price: {close_price}, Change: {price_change}%")
            return price_change
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise

def main():
    """
    Main function to handle the Ethereum price query for June 13, 2025, 1 AM ET.
    """
    try:
        # Date and time for the query
        date_str = "2025-06-13"
        hour = 1  # 1 AM ET
        timezone_str = "US/Eastern"
        
        # Get the price change percentage
        price_change = get_eth_price_at_specific_time(date_str, hour, 0, timezone_str)
        
        # Determine the resolution based on the price change
        if price_change >= 0:
            recommendation = "p2"  # Up
        else:
            recommendation = "p1"  # Down
        
        # Output the recommendation
        print(f"recommendation: {recommendation}")
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        # Default to p3 (unknown/50-50) in case of any errors
        print("recommendation: p3")

if __name__ == "__main__":
    main()