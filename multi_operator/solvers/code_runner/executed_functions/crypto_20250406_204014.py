import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def fetch_ethusdt_low_prices(start_date, end_date):
    """
    Fetches the low prices for ETHUSDT on Binance for the given date range.

    Args:
        start_date: Start date in datetime format
        end_date: End date in datetime format

    Returns:
        List of low prices
    """
    symbol = "ETHUSDT"
    interval = "1m"
    limit = 1000  # Maximum limit allowed by Binance for one request
    prices = []

    # Convert dates to milliseconds
    start_time = int(start_date.timestamp() * 1000)
    end_time = int(end_date.timestamp() * 1000)

    while start_time < end_time:
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
            "startTime": start_time,
            "endTime": end_time
        }
        response = requests.get("https://api.binance.com/api/v3/klines", params=params)
        response.raise_for_status()
        data = response.json()

        # Extract the low prices from the data
        for candle in data:
            low_price = float(candle[3])
            prices.append(low_price)

        # Update start_time to the last candle's close time
        if data:
            last_candle_close_time = data[-1][6]
            start_time = last_candle_close_time + 1
        else:
            break

    return prices

def check_eth_price_dip_to_target(prices, target_price):
    """
    Checks if the price of ETH dipped to or below the target price.

    Args:
        prices: List of low prices
        target_price: Target price to check

    Returns:
        Boolean indicating if the price dipped to or below the target price
    """
    return any(price <= target_price for price in prices)

def main():
    # Define the time range for April 2025 in ET timezone
    tz = pytz.timezone("US/Eastern")
    start_date = tz.localize(datetime(2025, 4, 1))
    end_date = tz.localize(datetime(2025, 4, 30, 23, 59, 59))

    # Convert to UTC
    start_date_utc = start_date.astimezone(pytz.utc)
    end_date_utc = end_date.astimezone(pytz.utc)

    # Fetch low prices for ETHUSDT from Binance
    low_prices = fetch_ethusdt_low_prices(start_date_utc, end_date_utc)

    # Check if the price dipped to $1600 or lower
    target_price = 1600.0
    price_dipped = check_eth_price_dip_to_target(low_prices, target_price)

    # Output the result
    if price_dipped:
        print("recommendation: p2")  # Yes, price dipped to $1600 or lower
    else:
        print("recommendation: p1")  # No, price did not dip to $1600 or lower

if __name__ == "__main__":
    main()