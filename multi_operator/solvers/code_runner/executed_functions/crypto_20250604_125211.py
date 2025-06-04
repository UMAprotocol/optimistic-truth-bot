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

def fetch_binance_data(symbol, interval, start_time, end_time):
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
        data = response.json()
        return data

def check_bitcoin_dip_to_90k(start_date, end_date):
    """
    Checks if Bitcoin dipped to $90,000 or lower between the given start and end dates.
    """
    # Convert dates to UTC timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d %H:%M"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d %H:%M"))

    start_timestamp = int(start_dt.timestamp() * 1000)
    end_timestamp = int(end_dt.timestamp() * 1000)

    # Fetch data from Binance
    data = fetch_binance_data("BTCUSDT", "1m", start_timestamp, end_timestamp)

    # Check if any low price is at or below $90,000
    for candle in data:
        low_price = float(candle[3])  # Low price is the fourth element in the list
        if low_price <= 90000:
            return True

    return False

def main():
    # Define the period to check for the Bitcoin price dip
    start_date = "2025-05-01 00:00"
    end_date = "2025-05-31 23:59"

    # Check if Bitcoin dipped to $90,000 or lower
    dipped_to_90k = check_bitcoin_dip_to_90k(start_date, end_date)

    # Print the result based on the dip status
    if dipped_to_90k:
        print("recommendation: p2")  # Yes, it dipped to $90,000 or lower
    else:
        print("recommendation: p1")  # No, it did not dip to $90,000 or lower

if __name__ == "__main__":
    main()