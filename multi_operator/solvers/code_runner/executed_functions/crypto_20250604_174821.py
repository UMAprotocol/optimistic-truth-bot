import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables
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
        "limit": 1000,  # Maximum limit
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint first
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
            return response.json()
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def check_bitcoin_dip_to_80k(start_date, end_date):
    """
    Checks if Bitcoin dipped to $80k or below between the given start and end dates.
    """
    # Convert dates to UTC timestamps
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(start_dt).astimezone(pytz.utc)
    end_dt = tz.localize(end_dt).astimezone(pytz.utc)

    # Convert datetime to milliseconds since epoch
    start_time = int(start_dt.timestamp() * 1000)
    end_time = int(end_dt.timestamp() * 1000)

    # Fetch data from Binance
    data = fetch_data_from_binance("BTCUSDT", "1m", start_time, end_time)

    # Check if any candle's low was at or below $80,000
    if data:
        for candle in data:
            low_price = float(candle[3])  # Low price is the fourth element in the list
            if low_price <= 80000:
                return True
    return False

def main():
    # Define the period to check for the Bitcoin price dip
    start_date = "2025-05-01"
    end_date = "2025-05-31"

    # Check if Bitcoin dipped to $80k or below
    dipped_to_80k = check_bitcoin_dip_to_80k(start_date, end_date)

    # Print the result based on the dip status
    if dipped_to_80k:
        print("recommendation: p2")  # Yes, it dipped to $80k or below
    else:
        print("recommendation: p1")  # No, it did not dip to $80k or below

if __name__ == "__main__":
    main()