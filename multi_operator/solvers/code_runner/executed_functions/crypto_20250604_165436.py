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
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_data_from_binance(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1000,  # Adjust based on the maximum allowed by the API
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data using the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def check_doge_price_dip_to_threshold(start_date, end_date, threshold):
    """
    Checks if the price of Dogecoin dipped to or below a certain threshold within a given date range.
    """
    # Convert dates to timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))
    
    start_ts = int(start_dt.timestamp() * 1000)
    end_ts = int(end_dt.timestamp() * 1000)
    
    # Fetch data
    data = fetch_data_from_binance("DOGEUSDT", "1m", start_ts, end_ts)
    
    if data:
        # Check if any low price in the data is below the threshold
        for candle in data:
            low_price = float(candle[3])  # Low price is the fourth element in the list
            if low_price <= threshold:
                return True
    return False

def main():
    # Define the date range and threshold for checking the price dip
    start_date = "2025-05-01"
    end_date = "2025-05-31"
    threshold = 0.12
    
    # Check if the price dipped to or below the threshold
    result = check_doge_price_dip_to_threshold(start_date, end_date, threshold)
    
    # Print the result based on the check
    if result:
        print("recommendation: p2")  # Yes, it dipped to $0.12 or lower
    else:
        print("recommendation: p1")  # No, it did not dip to $0.12 or lower

if __name__ == "__main__":
    main()