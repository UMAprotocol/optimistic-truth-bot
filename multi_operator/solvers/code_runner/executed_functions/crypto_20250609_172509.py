import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# API keys are not required for this specific task as we are accessing public endpoints
# However, if needed for other purposes, they can be loaded like this:
# BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

def fetch_hyperliquid_prices(start_date, end_date):
    """
    Fetches the lowest price of HYPE/USDC from Hyperliquid within the specified date range.
    
    Args:
        start_date (datetime): Start date of the period to check prices.
        end_date (datetime): End date of the period to check prices.
    
    Returns:
        float: The lowest price found, or None if no data could be fetched.
    """
    # Convert datetime to timestamps for the API call
    start_timestamp = int(start_date.timestamp() * 1000)  # Convert to milliseconds
    end_timestamp = int(end_date.timestamp() * 1000)  # Convert to milliseconds
    
    # Hyperliquid API endpoint for fetching historical data
    url = "https://app.hyperliquid.xyz/api/v1/historical"
    params = {
        "symbol": "HYPE/USDC",
        "resolution": "1m",
        "from": start_timestamp,
        "to": end_timestamp
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Extract the lowest price from the 'l' (low) prices in the data
        low_prices = [float(price) for price in data['l']]
        return min(low_prices) if low_prices else None
    
    except requests.RequestException as e:
        print(f"Failed to fetch data from Hyperliquid: {e}")
        return None

def main():
    # Define the time period to check
    start_date = datetime(2025, 5, 7, 16, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Fetch the lowest price of HYPE/USDC during the specified period
    lowest_price = fetch_hyperliquid_prices(start_date, end_date)
    
    # Determine the resolution based on the lowest price found
    if lowest_price is not None and lowest_price <= 10.0:
        print("recommendation: p2")  # Yes, the price dipped to $10 or lower
    else:
        print("recommendation: p1")  # No, the price did not dip to $10 or lower

if __name__ == "__main__":
    main()