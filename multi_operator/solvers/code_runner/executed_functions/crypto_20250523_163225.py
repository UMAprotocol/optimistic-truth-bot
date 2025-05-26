import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def fetch_hyperliquid_price(date_str, symbol="HYPE/USDC", interval="1m"):
    """
    Fetches the close price of a cryptocurrency pair from Hyperliquid for a specific minute.
    
    Args:
        date_str (str): Date and time string in "YYYY-MM-DD HH:MM" format.
        symbol (str): Symbol of the cryptocurrency pair.
        interval (str): Interval of the candle data.
    
    Returns:
        float: The close price of the cryptocurrency.
    """
    # Convert date_str to the appropriate timestamp for the API call
    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    dt = pytz.timezone("US/Eastern").localize(dt)
    timestamp = int(dt.timestamp() * 1000)  # Convert to milliseconds

    # Construct the API URL
    url = f"https://app.hyperliquid.xyz/api/v1/candles?symbol={symbol}&interval={interval}&startTime={timestamp}&endTime={timestamp + 60000}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data and 'candles' in data and data['candles']:
            close_price = float(data['candles'][0]['close'])
            return close_price
        else:
            logger.error("No data available for the specified time.")
            return None
    except requests.RequestException as e:
        logger.error(f"Failed to fetch data from Hyperliquid: {str(e)}")
        return None

def compare_prices(price1, price2):
    """
    Compares two prices and determines the market resolution based on the comparison.
    
    Args:
        price1 (float): Price from the first day.
        price2 (float): Price from the second day.
    
    Returns:
        str: Market resolution ('p1', 'p2', 'p3').
    """
    if price1 is None or price2 is None:
        return "p4"  # Unable to resolve due to missing data
    if price1 < price2:
        return "p2"  # Up
    elif price1 > price2:
        return "p1"  # Down
    else:
        return "p3"  # 50-50

def main():
    # Define the dates and times for price comparison
    date1 = "2025-05-22 12:00"
    date2 = "2025-05-23 12:00"

    # Fetch prices from Hyperliquid
    price1 = fetch_hyperliquid_price(date1)
    price2 = fetch_hyperliquid_price(date2)

    # Compare prices and determine the resolution
    resolution = compare_prices(price1, price2)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()