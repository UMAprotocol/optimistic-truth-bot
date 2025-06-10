import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# API keys are not used in this script as the required data is publicly accessible
# However, if needed, they can be loaded like this:
# BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

def fetch_fartcoin_prices(start_date, end_date):
    """
    Fetches the 1-minute candle low prices for Fartcoin/SOL on Dexscreener between specified dates.
    
    Args:
        start_date (datetime): Start date and time in UTC.
        end_date (datetime): End date and time in UTC.
    
    Returns:
        list of floats: List of low prices during the period.
    """
    url = "https://dexscreener.com/solana/bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"
    params = {
        "from": int(start_date.timestamp()),
        "to": int(end_date.timestamp()),
        "resolution": "1m"  # 1 minute resolution
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        low_prices = [float(candle['l']) for candle in data['data']]
        return low_prices
    except requests.RequestException as e:
        print(f"Failed to fetch data: {e}")
        return []

def check_price_dip_to_threshold(low_prices, threshold=0.40):
    """
    Checks if any of the prices in the list dips to or below the threshold.
    
    Args:
        low_prices (list of float): List of low prices.
        threshold (float): Threshold price to check against.
    
    Returns:
        bool: True if any price dips to or below the threshold, False otherwise.
    """
    return any(price <= threshold for price in low_prices)

def main():
    # Define the time period for the query
    start_date = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Convert time to UTC
    start_date_utc = start_date.astimezone(pytz.utc)
    end_date_utc = end_date.astimezone(pytz.utc)
    
    # Fetch prices
    low_prices = fetch_fartcoin_prices(start_date_utc, end_date_utc)
    
    # Check if the price dipped to $0.40 or lower
    if check_price_dip_to_threshold(low_prices):
        print("recommendation: p2")  # Yes, it dipped to $0.40 or lower
    else:
        print("recommendation: p1")  # No, it did not dip to $0.40 or lower

if __name__ == "__main__":
    main()