import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_ENDPOINT = "https://api.binance.com/api/v3/klines"
PROXY_API_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from Binance API for a given symbol within a specified time range.
    Implements a fallback from proxy to primary endpoint in case of failure.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_ENDPOINT, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def check_price_dip_to_threshold(symbol, start_date, end_date, threshold_price):
    """
    Checks if the price of a given symbol dips to or below a threshold price between start_date and end_date.
    """
    # Convert dates to timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d %H:%M"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d %H:%M"))
    
    start_timestamp = int(start_dt.timestamp() * 1000)
    end_timestamp = int(end_dt.timestamp() * 1000)
    
    # Fetch price data
    data = fetch_price_data(symbol, start_timestamp, end_timestamp)
    
    if data:
        # Check if any 'Low' price in the data dips to or below the threshold
        for candle in data:
            low_price = float(candle[3])  # 'Low' price is the fourth element in each candle
            if low_price <= threshold_price:
                return True
    return False

def main():
    """
    Main function to determine if SUI dipped to $3.0 in May 2025.
    """
    symbol = "SUIUSDT"
    start_date = "2025-05-07 00:00"
    end_date = "2025-05-31 23:59"
    threshold_price = 3.0
    
    if check_price_dip_to_threshold(symbol, start_date, end_date, threshold_price):
        print("recommendation: p2")  # Yes, price dipped to $3.0 or lower
    else:
        print("recommendation: p1")  # No, price did not dip to $3.0 or lower

if __name__ == "__main__":
    main()