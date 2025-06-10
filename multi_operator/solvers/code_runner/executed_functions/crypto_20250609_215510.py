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

def fetch_data_from_binance(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Maximum allowed by Binance
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

def check_solana_price_threshold(start_date, end_date, threshold):
    """
    Checks if Solana's price reached a certain threshold between two dates.
    """
    # Convert dates to UTC timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d %H:%M"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d %H:%M"))
    
    start_ts = int(start_dt.timestamp() * 1000)
    end_ts = int(end_dt.timestamp() * 1000)
    
    # Fetch data
    data = fetch_data_from_binance("SOLUSDT", start_ts, end_ts)
    
    if data:
        for candle in data:
            high_price = float(candle[2])  # High price is the third element in the list
            if high_price >= threshold:
                return True
    return False

def main():
    # Define the period and threshold
    start_date = "2025-05-01 00:00"
    end_date = "2025-05-31 23:59"
    price_threshold = 190.00
    
    # Check if the price threshold was reached
    result = check_solana_price_threshold(start_date, end_date, price_threshold)
    
    # Print the result based on the check
    if result:
        print("recommendation: p2")  # Yes, Solana reached $190 or higher
    else:
        print("recommendation: p1")  # No, Solana did not reach $190

if __name__ == "__main__":
    main()