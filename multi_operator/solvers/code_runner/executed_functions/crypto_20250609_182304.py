import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_ENDPOINT = "https://api.binance.com/api/v3/klines"
PROXY_API_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_data_from_binance(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1000  # Adjust based on the maximum number of data points needed
    }
    
    try:
        # Try fetching data using the proxy endpoint
        response = requests.get(PROXY_API_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def check_bitcoin_dip_to_threshold(start_date, end_date, threshold_price):
    """
    Checks if Bitcoin price dipped to or below a threshold price within a given date range.
    """
    # Convert dates to UTC timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))
    
    start_timestamp = int(start_dt.timestamp() * 1000)
    end_timestamp = int(end_dt.timestamp() * 1000)
    
    # Fetch data
    data = fetch_data_from_binance("BTCUSDT", "1m", start_timestamp, end_timestamp)
    
    # Check if any low price in the data is below the threshold
    for candle in data:
        low_price = float(candle[3])  # Low price is the fourth element in the list
        if low_price <= threshold_price:
            return True
    
    return False

def main():
    # Define the date range and threshold price
    start_date = "2025-05-01"
    end_date = "2025-05-31"
    threshold_price = 70000
    
    # Check if Bitcoin dipped to or below the threshold price
    dipped = check_bitcoin_dip_to_threshold(start_date, end_date, threshold_price)
    
    # Print the result based on the dip status
    if dipped:
        print("recommendation: p2")  # Yes, Bitcoin dipped to $70k or lower
    else:
        print("recommendation: p1")  # No, Bitcoin did not dip to $70k or lower

if __name__ == "__main__":
    main()