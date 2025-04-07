import requests
from datetime import datetime, timedelta
import pytz

def fetch_btc_prices():
    # Define the URL for Binance API to fetch historical data
    base_url = "https://api.binance.com/api/v3/klines"
    symbol = "BTCUSDT"
    interval = "1m"
    start_time = "2025-04-01T00:00:00"
    end_time = "2025-04-30T23:59:00"
    limit = 1000  # Maximum limit per API call

    # Convert times to milliseconds for API parameters
    start_time = int(datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.timezone('US/Eastern')).timestamp() * 1000)
    end_time = int(datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.timezone('US/Eastern')).timestamp() * 1000)

    # Initialize parameters for API call
    params = {
        'symbol': symbol,
        'interval': interval,
        'startTime': start_time,
        'endTime': end_time,
        'limit': limit
    }

    try:
        # Fetch data from Binance API
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        # Check each candle if the low price is $80,000 or lower
        for candle in data:
            low_price = float(candle[3])  # Low price is the fourth item in the list
            if low_price <= 80000:
                return "recommendation: p2"  # Yes, price dipped to $80k or lower

        return "recommendation: p1"  # No, price did not dip to $80k or lower

    except requests.RequestException as e:
        print(f"Error fetching data from Binance: {e}")
        return "recommendation: p3"  # Unknown/50-50 due to error

# Run the function and print the result
result = fetch_btc_prices()
print(result)