import os
import requests
from datetime import datetime, timedelta
from pytz import timezone

def check_ethereum_dip():
    # Load environment variables
    api_key = os.getenv('BINANCE_API_KEY')
    
    # Define the time period for the query
    start_date = datetime(2025, 4, 1, 0, 0, 0, tzinfo=timezone('US/Eastern'))
    end_date = datetime(2025, 4, 30, 23, 59, 59, tzinfo=timezone('US/Eastern'))
    
    # Convert dates to timestamps
    start_timestamp = int(start_date.timestamp() * 1000)
    end_timestamp = int(end_date.timestamp() * 1000)
    
    # Binance API endpoint for historical data
    url = "https://api.binance.com/api/v3/klines"
    
    # Parameters for the API request
    params = {
        'symbol': 'ETHUSDT',
        'interval': '1m',
        'startTime': start_timestamp,
        'endTime': end_timestamp,
        'limit': 1000  # Maximum limit per API call
    }
    
    # Headers for the API request
    headers = {
        'X-MBX-APIKEY': api_key
    }
    
    try:
        # Initial API call
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Check if any candle's low price is $1600 or lower
        for candle in data:
            low_price = float(candle[3])  # Low price is the fourth item in the list
            if low_price <= 1600:
                return "recommendation: p2"  # p2 corresponds to Yes
        
        # If no candle meets the condition, return No
        return "recommendation: p1"  # p1 corresponds to No
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return "recommendation: p3"  # p3 corresponds to unknown/50-50 if there's an error

# Example usage
if __name__ == "__main__":
    recommendation = check_ethereum_dip()
    print(recommendation)