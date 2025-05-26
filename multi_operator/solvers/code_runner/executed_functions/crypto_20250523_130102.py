import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
HYPE_USDC_SYMBOL = "HYPEUSDC"
HYPERLIQUID_BASE_URL = "https://app.hyperliquid.xyz/api"
HYPERLIQUID_ENDPOINT = "/trade/candles"

# Timezone conversion
ET_TIMEZONE = pytz.timezone('US/Eastern')
UTC_TIMEZONE = pytz.timezone('UTC')

def fetch_candles(symbol, start_time, end_time, interval='1m'):
    """
    Fetches candle data from Hyperliquid for a given symbol within a specified time range.
    """
    url = f"{HYPERLIQUID_BASE_URL}{HYPERLIQUID_ENDPOINT}"
    params = {
        'symbol': symbol,
        'interval': interval,
        'startTime': int(start_time.timestamp() * 1000),  # Convert to milliseconds
        'endTime': int(end_time.timestamp() * 1000)  # Convert to milliseconds
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch data: {e}")
        return None

def find_highest_price(candles):
    """
    Finds the highest price from a list of candle data.
    """
    highest_price = 0
    for candle in candles:
        # Assuming candle data format is [timestamp, open, high, low, close]
        high_price = float(candle[2])
        if high_price > highest_price:
            highest_price = high_price
    return highest_price

def main():
    # Define the time range for the query
    start_date = datetime(2025, 5, 22, 12, 0, tzinfo=ET_TIMEZONE)
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=ET_TIMEZONE)
    
    # Convert time to UTC
    start_date_utc = start_date.astimezone(UTC_TIMEZONE)
    end_date_utc = end_date.astimezone(UTC_TIMEZONE)
    
    # Fetch historical candles to find the highest price before the start date
    historical_end_date = start_date_utc - timedelta(minutes=1)  # One minute before the start date
    historical_candles = fetch_candles(HYPE_USDC_SYMBOL, datetime(2020, 1, 1, tzinfo=UTC_TIMEZONE), historical_end_date)
    if historical_candles is None:
        logging.error("Failed to fetch historical data.")
        print("recommendation: p4")
        return
    
    highest_historical_price = find_highest_price(historical_candles)
    
    # Fetch candles for the specified period
    period_candles = fetch_candles(HYPE_USDC_SYMBOL, start_date_utc, end_date_utc)
    if period_candles is None:
        logging.error("Failed to fetch period data.")
        print("recommendation: p4")
        return
    
    highest_period_price = find_highest_price(period_candles)
    
    # Determine the resolution based on the highest prices
    if highest_period_price > highest_historical_price:
        print("recommendation: p2")  # Yes, new all-time high
    else:
        print("recommendation: p1")  # No, no new all-time high

if __name__ == "__main__":
    main()