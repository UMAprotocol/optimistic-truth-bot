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

def check_solana_price_threshold(start_date, end_date, threshold):
    """
    Checks if the price of Solana ever reaches or exceeds the threshold within the given date range.
    """
    # Convert dates to UTC timestamps
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # Include the end date fully
    start_ts = int(start_dt.replace(tzinfo=pytz.UTC).timestamp() * 1000)
    end_ts = int(end_dt.replace(tzinfo=pytz.UTC).timestamp() * 1000)

    # Fetch price data
    data = fetch_price_data("SOLUSDT", start_ts, end_ts)
    if data:
        for candle in data:
            high_price = float(candle[2])  # High price is at index 2 in each candle
            if high_price >= threshold:
                return True
    return False

def main():
    """
    Main function to determine if Solana reaches $160 in June 2025.
    """
    result = check_solana_price_threshold("2025-06-01", "2025-06-30", 160)
    if result:
        print("recommendation: p2")  # Yes, Solana reached $160
    else:
        print("recommendation: p1")  # No, Solana did not reach $160

if __name__ == "__main__":
    main()