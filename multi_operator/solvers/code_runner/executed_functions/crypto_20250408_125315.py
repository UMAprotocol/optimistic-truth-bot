import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def check_ethereum_dip_to_1600():
    """
    Checks if Ethereum (ETHUSDT) dipped to $1600 or lower in April 2025 on Binance.
    Uses the Binance API to fetch historical 1-minute candle data for the ETHUSDT pair.
    """
    # Define the time period for April 2025 in Eastern Time
    start_date = datetime(2025, 4, 1, 0, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 4, 30, 23, 59, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Convert start and end dates to UTC since Binance API requires UTC
    start_date_utc = start_date.astimezone(pytz.utc)
    end_date_utc = end_date.astimezone(pytz.utc)
    
    # Convert datetime to milliseconds since this is what Binance API expects
    start_time_ms = int(start_date_utc.timestamp() * 1000)
    end_time_ms = int(end_date_utc.timestamp() * 1000)
    
    # Binance API endpoint for historical klines (candles)
    url = "https://api.binance.com/api/v3/klines"
    
    # Parameters for the API call
    params = {
        "symbol": "ETHUSDT",
        "interval": "1m",
        "startTime": start_time_ms,
        "endTime": end_time_ms,
        "limit": 1000  # Maximum limit per API call
    }
    
    try:
        # Loop through the entire month, fetching data in chunks
        while start_time_ms < end_time_ms:
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raise an exception for HTTP errors
            data = response.json()
            
            # Check each candle to see if the low price was $1600 or lower
            for candle in data:
                low_price = float(candle[3])  # Low price is the fourth element in the list
                if low_price <= 1600:
                    return "Yes, Ethereum dipped to $1600 or lower in April 2025."
            
            # Update startTime for the next API call
            last_candle_time = int(data[-1][6])  # End time of the last candle received
            params['startTime'] = last_candle_time + 1
            
            # Prevent hitting the API rate limit
            time.sleep(0.5)
        
        return "No, Ethereum did not dip to $1600 in April 2025."
    except Exception as e:
        return f"An error occurred: {str(e)}"

def main():
    result = check_ethereum_dip_to_1600()
    print(result)

if __name__ == "__main__":
    main()