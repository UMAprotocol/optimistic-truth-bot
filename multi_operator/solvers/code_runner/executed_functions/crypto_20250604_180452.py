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
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from Binance API for a given symbol within a specified time range.
    Implements a fallback mechanism from proxy to primary API endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Maximum limit
        "startTime": start_time,
        "endTime": end_time
    }

    try:
        # Try fetching data from the proxy endpoint
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

def check_price_dip_to_threshold(symbol, start_date, end_date, threshold):
    """
    Checks if the price of a cryptocurrency dipped to or below a certain threshold within a given date range.
    """
    # Convert dates to timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))

    start_ts = int(start_dt.timestamp() * 1000)
    end_ts = int(end_dt.timestamp() * 1000)

    # Fetch price data
    price_data = fetch_price_data(symbol, start_ts, end_ts)

    if price_data:
        # Check if any 'Low' price in the data dips to or below the threshold
        for candle in price_data:
            low_price = float(candle[3])  # 'Low' price is at index 3
            if low_price <= threshold:
                return True
    return False

def main():
    """
    Main function to determine if Solana (SOLUSDT) dipped to $140 or below in May 2025.
    """
    symbol = "SOLUSDT"
    start_date = "2025-05-01"
    end_date = "2025-05-31"
    threshold = 140.00

    result = check_price_dip_to_threshold(symbol, start_date, end_date, threshold)
    if result:
        print("recommendation: p2")  # Yes, it dipped to $140 or below
    else:
        print("recommendation: p1")  # No, it did not dip to $140 or below

if __name__ == "__main__":
    main()