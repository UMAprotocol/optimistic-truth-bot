import requests
from datetime import datetime, timedelta
from pytz import timezone

def fetch_ethereum_low_prices():
    # Define the URL and parameters for the API request
    url = "https://api.binance.com/api/v3/klines"
    start_time = int(datetime(2025, 4, 1, 0, 0, 0, tzinfo=timezone('US/Eastern')).timestamp() * 1000)
    end_time = int(datetime(2025, 4, 30, 23, 59, 59, tzinfo=timezone('US/Eastern')).timestamp() * 1000)
    params = {
        'symbol': 'ETHUSDT',
        'interval': '1m',
        'startTime': start_time,
        'endTime': end_time,
        'limit': 1000  # Maximum limit allowed by Binance API
    }

    try:
        # Fetch data from Binance API
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Extract the low prices from the data
        low_prices = [float(candle[3]) for candle in data]

        return low_prices
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def check_ethereum_price_dip():
    low_prices = fetch_ethereum_low_prices()
    if low_prices is None:
        return "recommendation: p3"  # Unable to fetch data, return unknown/50-50

    # Check if any price dipped to $1600 or lower
    for price in low_prices:
        if price <= 1600.00:
            return "recommendation: p2"  # Yes, price dipped to $1600 or lower

    return "recommendation: p1"  # No, price did not dip to $1600 or lower

# Check if the current date is within the specified range
current_date = datetime.now(timezone('US/Eastern'))
if current_date < datetime(2025, 4, 1, 0, 0, tzinfo=timezone('US/Eastern')) or current_date > datetime(2025, 4, 30, 23, 59, tzinfo=timezone('US/Eastern')):
    print("recommendation: p4")  # Too early or too late to resolve
else:
    # Perform the check and print the recommendation
    print(check_ethereum_price_dip())