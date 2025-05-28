import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Define the API endpoints
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Define the API key environment variable
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

def fetch_data_from_proxy(symbol, interval, start_time, end_time):
    """
    Fetch data using the proxy endpoint with fallback to the primary endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def convert_to_utc_timestamp(date_str, time_str, timezone_str):
    """
    Convert local time to UTC timestamp in milliseconds.
    """
    tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    local_dt = tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def check_bitcoin_hashprice():
    """
    Check if the Bitcoin hashprice reached $57.50 between May 19, 2025, 18:00 and May 31, 2025, 23:59 ET.
    """
    start_date = "2025-05-19 18:00:00"
    end_date = "2025-05-31 23:59:00"
    start_timestamp = convert_to_utc_timestamp(start_date.split()[0], start_date.split()[1], "US/Eastern")
    end_timestamp = convert_to_utc_timestamp(end_date.split()[0], end_date.split()[1], "US/Eastern")

    # Fetch data for the specified period
    data = fetch_data_from_proxy("BTCUSDT", "1m", start_timestamp, end_timestamp)

    # Check if any price reached $57.50001 or higher
    for item in data:
        close_price = float(item[4])
        if close_price >= 57.50001:
            return "p2"  # Yes, it reached $57.50 or higher

    return "p1"  # No, it did not reach $57.50

def main():
    """
    Main function to execute the check.
    """
    result = check_bitcoin_hashprice()
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()