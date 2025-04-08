import requests
from datetime import datetime, timedelta
from pytz import timezone

def fetch_ethereum_prices():
    # Define the URL and parameters for the API request
    url = "https://api.binance.com/api/v3/klines"
    start_time = datetime(2025, 4, 1, 0, 0, 0, tzinfo=timezone('US/Eastern'))
    end_time = datetime(2025, 4, 30, 23, 59, 59, tzinfo=timezone('US/Eastern'))
    params = {
        'symbol': 'ETHUSDT',
        'interval': '1m',
        'startTime': int(start_time.timestamp() * 1000),
        'endTime': int(end_time.timestamp() * 1000)
    }

    # Make the API request
    response = requests.get(url, params=params)
    data = response.json()

    # Check if Ethereum dipped to $1600 or lower
    for candle in data:
        low_price = float(candle[3])  # Low price is the fourth item in the list
        if low_price <= 1600.00:
            return True

    return False

def main():
    current_time = datetime.now(timezone('US/Eastern'))
    market_end_time = datetime(2025, 4, 30, 23, 59, 59, tzinfo=timezone('US/Eastern'))

    # Check if the current time is before the market end time
    if current_time > market_end_time:
        # Fetch Ethereum prices and determine if it dipped to $1600 or lower
        if fetch_ethereum_prices():
            print("recommendation: p2")  # Yes, it dipped to $1600 or lower
        else:
            print("recommendation: p1")  # No, it did not dip to $1600 or lower
    else:
        print("recommendation: p4")  # Too early to resolve

if __name__ == "__main__":
    main()