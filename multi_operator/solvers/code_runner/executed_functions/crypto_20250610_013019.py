import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

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
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_ENDPOINT, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def check_bitcoin_dip_to_60k():
    """
    Checks if Bitcoin dipped to $60k or below in May 2025.
    """
    # Define the time period for May 2025 in Eastern Time
    start_date = datetime(2025, 5, 1, 0, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, 59, tzinfo=pytz.timezone('US/Eastern'))

    # Convert to UTC timestamps
    start_timestamp = int(start_date.timestamp() * 1000)
    end_timestamp = int(end_date.timestamp() * 1000)

    # Fetch data from Binance
    data = fetch_data_from_binance("BTCUSDT", "1m", start_timestamp, end_timestamp)

    if data:
        # Check if any candle's low price was $60,000 or lower
        for candle in data:
            low_price = float(candle[3])  # Low price is the fourth element in the list
            if low_price <= 60000:
                print("recommendation: p2")  # Yes, Bitcoin dipped to $60k or below
                return
        print("recommendation: p1")  # No, Bitcoin did not dip to $60k or below
    else:
        print("recommendation: p4")  # Unable to determine due to data fetch failure

if __name__ == "__main__":
    check_bitcoin_dip_to_60k()