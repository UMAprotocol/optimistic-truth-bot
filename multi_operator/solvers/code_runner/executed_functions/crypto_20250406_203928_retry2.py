import os
import requests
from datetime import datetime, timedelta
from python_dotenv import load_dotenv

def check_ethereum_dip():
    load_dotenv()  # Load environment variables from .env file
    api_key = os.getenv('BINANCE_API_KEY')  # Assuming API key is stored in .env file
    base_url = "https://api.binance.com/api/v3/klines"
    symbol = "ETHUSDT"
    interval = "1m"
    start_time = int(datetime(2025, 4, 1, 0, 0).timestamp() * 1000)
    end_time = int(datetime(2025, 4, 30, 23, 59).timestamp() * 1000)
    limit = 1000  # Maximum limit allowed by Binance API for one request

    headers = {
        'X-MBX-APIKEY': api_key
    }

    params = {
        'symbol': symbol,
        'interval': interval,
        'startTime': start_time,
        'endTime': end_time,
        'limit': limit
    }

    try:
        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        # Check if any candle's low price is $1600 or lower
        for candle in data:
            low_price = float(candle[3])  # Low price is the fourth item in the list
            if low_price <= 1600:
                return "recommendation: p2"  # p2 corresponds to "Yes"

        return "recommendation: p1"  # p1 corresponds to "No"

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return "recommendation: p3"  # p3 corresponds to unknown/50-50 outcome

# Run the function and print the result
print(check_ethereum_dip())