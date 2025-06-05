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

def check_doge_price_dip_to_threshold(start_date, end_date, threshold_price=0.05):
    """
    Checks if the price of Dogecoin dipped to or below a certain threshold within a given date range.
    """
    # Convert dates to timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))
    
    start_timestamp = int(start_dt.timestamp() * 1000)
    end_timestamp = int(end_dt.timestamp() * 1000) - 1  # Subtract 1 millisecond to include the end of the last day
    
    # Fetch data from Binance
    data = fetch_data_from_binance("DOGEUSDT", start_timestamp, end_timestamp)
    
    if data:
        # Check if any candle's low price is at or below the threshold
        for candle in data:
            low_price = float(candle[3])  # Low price is the fourth element in the list
            if low_price <= threshold_price:
                return True
    return False

def main():
    """
    Main function to determine if Dogecoin dipped to $0.05 in May 2025.
    """
    result = check_doge_price_dip_to_threshold("2025-05-01", "2025-05-31")
    if result:
        print("recommendation: p2")  # Yes, it dipped to $0.05 or lower
    else:
        print("recommendation: p1")  # No, it did not dip to $0.05 or lower

if __name__ == "__main__":
    main()