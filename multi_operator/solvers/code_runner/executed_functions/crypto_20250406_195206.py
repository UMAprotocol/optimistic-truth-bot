import requests
from datetime import datetime, timedelta
import pytz

def fetch_solana_price_data():
    # Define the time range for April 2025 in Eastern Time
    start_date = datetime(2025, 4, 1, 0, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 4, 30, 23, 59, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Convert to UTC since Binance uses UTC
    start_date_utc = start_date.astimezone(pytz.utc)
    end_date_utc = end_date.astimezone(pytz.utc)
    
    # Format timestamps for Binance API
    start_timestamp = int(start_date_utc.timestamp() * 1000)
    end_timestamp = int(end_date_utc.timestamp() * 1000)
    
    # Binance API endpoint for historical klines
    url = "https://api.binance.com/api/v3/klines"
    
    # Parameters for the API request
    params = {
        'symbol': 'SOLUSDT',
        'interval': '1m',
        'startTime': start_timestamp,
        'endTime': end_timestamp,
        'limit': 1000  # Maximum limit per API call
    }
    
    try:
        # Initialize variables
        lowest_price_found = float('inf')
        is_below_threshold = False
        
        # Loop to handle pagination in API response
        while True:
            response = requests.get(url, params=params)
            data = response.json()
            
            # Check if data is empty, which means we've reached the end of the available data
            if not data:
                break
            
            # Process each candle
            for candle in data:
                low_price = float(candle[3])  # Low price is the fourth element in the list
                if low_price < lowest_price_found:
                    lowest_price_found = low_price
                if low_price <= 110.00:
                    is_below_threshold = True
                    break
            
            # Break the loop if price threshold is met
            if is_below_threshold:
                break
            
            # Update startTime for the next API call to continue where the last call left off
            last_open_time = data[-1][0]
            params['startTime'] = last_open_time + 60000  # Move to the next minute
        
        # Return recommendation based on the lowest price found
        if is_below_threshold:
            return "recommendation: p2"  # Yes, price dipped to $110 or lower
        else:
            return "recommendation: p1"  # No, price did not dip to $110 or lower
    except Exception as e:
        print(f"An error occurred: {e}")
        return "recommendation: p3"  # Unknown/50-50 due to error

# Run the function and print the result
print(fetch_solana_price_data())