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

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from Binance API for a given symbol within a specified time range.
    Implements a fallback mechanism from proxy to primary API endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Maximum allowed by Binance for one request
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

def check_solana_dip_to_110(start_date, end_date):
    """
    Checks if Solana (SOLUSDT) dipped to $110 or below between two dates.
    """
    # Convert dates to UTC timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d %H:%M"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d %H:%M"))

    start_timestamp = int(start_dt.timestamp() * 1000)
    end_timestamp = int(end_dt.timestamp() * 1000)

    # Fetch price data
    data = fetch_price_data("SOLUSDT", start_timestamp, end_timestamp)

    if data:
        for candle in data:
            low_price = float(candle[3])  # Low price is the fourth element in the list
            if low_price <= 110.00:
                return True
    return False

def main():
    """
    Main function to determine if Solana dipped to $110 in May 2025.
    """
    result = check_solana_dip_to_110("2025-05-01 00:00", "2025-05-31 23:59")
    if result:
        print("recommendation: p2")  # Yes, it dipped to $110 or below
    else:
        print("recommendation: p1")  # No, it did not dip to $110 or below

if __name__ == "__main__":
    main()