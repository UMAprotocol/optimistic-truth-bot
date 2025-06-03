import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

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
        print(f"Proxy failed with error: {e}, trying primary endpoint.")
        # Fallback to the primary API endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed with error: {e}")
            return None

def check_xrp_price_threshold(start_date, end_date, threshold):
    """
    Checks if the XRP price reaches a certain threshold within a given date range.
    """
    # Convert dates to timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))
    
    start_ts = int(start_dt.timestamp() * 1000)
    end_ts = int(end_dt.timestamp() * 1000)
    
    # Fetch data from Binance
    data = fetch_data_from_binance("XRPUSDT", start_ts, end_ts)
    
    if data:
        # Check if any high price in the data exceeds the threshold
        for candle in data:
            high_price = float(candle[2])  # High price is the third element in the list
            if high_price >= threshold:
                return True
    return False

def main():
    """
    Main function to determine if XRP reached $2.2 in June 2025.
    """
    result = check_xrp_price_threshold("2025-06-01", "2025-06-30", 2.2)
    if result:
        print("recommendation: p2")  # Yes, XRP reached $2.2
    else:
        print("recommendation: p1")  # No, XRP did not reach $2.2

if __name__ == "__main__":
    main()