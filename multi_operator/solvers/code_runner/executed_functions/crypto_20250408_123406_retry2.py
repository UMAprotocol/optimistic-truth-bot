import requests
from datetime import datetime
from pytz import timezone

def check_ethereum_price_dip():
    # Define the URL and parameters for the API request
    url = "https://api.binance.com/api/v3/klines"
    symbol = "ETHUSDT"
    interval = "1m"
    start_time = int(datetime(2025, 4, 1, 0, 0, 0, tzinfo=timezone('US/Eastern')).timestamp() * 1000)
    end_time = int(datetime(2025, 4, 30, 23, 59, 59, tzinfo=timezone('US/Eastern')).timestamp() * 1000)
    limit = 1000  # Maximum limit allowed by Binance API for one request

    # Initialize variables
    current_time = datetime.now(timezone('US/Eastern'))
    target_price = 1600.0
    reached_target = False

    # Check if the current date is within the April 2025 range
    if current_time < datetime(2025, 4, 1, 0, 0, 0, tzinfo=timezone('US/Eastern')) or current_time > datetime(2025, 4, 30, 23, 59, 59, tzinfo=timezone('US/Eastern')):
        return "recommendation: p4"  # Too early to resolve

    # Loop through the month of April 2025
    while start_time < end_time:
        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': start_time,
            'limit': limit
        }
        response = requests.get(url, params=params)
        data = response.json()

        # Check each candle for a low price of $1600 or lower
        for candle in data:
            low_price = float(candle[3])  # Low price is the fourth item in the list
            if low_price <= target_price:
                reached_target = True
                break

        # Update start_time to the last candle's close time for the next API call
        if data:
            start_time = int(data[-1][6]) + 1  # Close time of the last candle is the seventh item

        if reached_target:
            break

    # Return the appropriate recommendation based on whether the target price was reached
    if reached_target:
        return "recommendation: p2"  # Yes, Ethereum dipped to $1600 or lower
    else:
        return "recommendation: p1"  # No, Ethereum did not dip to $1600 or lower

# Run the function and print the result
print(check_ethereum_price_dip())