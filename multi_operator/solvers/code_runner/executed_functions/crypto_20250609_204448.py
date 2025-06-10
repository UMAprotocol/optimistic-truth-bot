import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_URL = "https://api.binance.com/api/v3"

def fetch_price_from_proxy(symbol, start_time, end_time):
    """ Fetch price using the proxy endpoint """
    try:
        response = requests.get(
            f"{PROXY_URL}/klines",
            params={
                "symbol": symbol,
                "interval": "1m",
                "limit": 1,
                "startTime": start_time,
                "endTime": end_time
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return float(data[0][3])  # Low price
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}")
        return None

def fetch_price_from_primary(symbol, start_time, end_time):
    """ Fetch price using the primary endpoint """
    try:
        response = requests.get(
            f"{PRIMARY_URL}/klines",
            params={
                "symbol": symbol,
                "interval": "1m",
                "limit": 1,
                "startTime": start_time,
                "endTime": end_time
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return float(data[0][3])  # Low price
    except Exception as e:
        print(f"Primary endpoint failed: {str(e)}")
        return None

def get_low_price(symbol, target_date, target_time):
    """ Get the low price for the symbol at the specified date and time """
    dt = datetime.strptime(f"{target_date} {target_time}", "%Y-%m-%d %H:%M:%S")
    start_time = int(dt.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later

    # Try fetching from proxy first
    price = fetch_price_from_proxy(symbol, start_time, end_time)
    if price is not None:
        return price

    # Fallback to primary if proxy fails
    return fetch_price_from_primary(symbol, start_time, end_time)

def main():
    # Define the parameters for the query
    symbol = "FARTSOL"
    target_date = "2025-05-31"
    target_time = "23:59:00"
    threshold_price = 0.85

    # Fetch the low price
    low_price = get_low_price(symbol, target_date, target_time)

    # Determine the resolution based on the fetched price
    if low_price is not None and low_price <= threshold_price:
        print("recommendation: p2")  # Yes, price dipped to $0.85 or lower
    else:
        print("recommendation: p1")  # No, price did not dip to $0.85 or lower

if __name__ == "__main__":
    main()