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

def fetch_data_from_proxy(symbol, start_time, end_time):
    """ Fetch data using the proxy endpoint """
    try:
        response = requests.get(
            f"{PROXY_URL}/klines",
            params={
                "symbol": symbol,
                "interval": "1m",
                "limit": 5,
                "startTime": start_time,
                "endTime": end_time
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        return None

def fetch_data_from_primary(symbol, start_time, end_time):
    """ Fetch data using the primary endpoint """
    try:
        response = requests.get(
            f"{PRIMARY_URL}/klines",
            params={
                "symbol": symbol,
                "interval": "1m",
                "limit": 5,
                "startTime": start_time,
                "endTime": end_time
            },
            headers={"X-MBX-APIKEY": BINANCE_API_KEY},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Primary endpoint failed: {str(e)}")
        return None

def check_fartcoin_fdv(symbol, start_time, end_time, target_fdv):
    """ Check if Fartcoin's FDV reached the target within the specified time frame """
    data = fetch_data_from_proxy(symbol, start_time, end_time)
    if not data:
        data = fetch_data_from_primary(symbol, start_time, end_time)
    if not data:
        return "p4"  # Unable to fetch data

    total_supply = 1000000000  # Example total supply, this should be fetched or defined based on actual data
    consecutive = 0
    for candle in data:
        low_price = float(candle[3])
        fdv = low_price * total_supply
        if fdv >= target_fdv:
            consecutive += 1
        else:
            consecutive = 0
        if consecutive >= 5:
            return "p2"  # Yes, FDV reached

    return "p1"  # No, FDV not reached

def main():
    symbol = "FARTUSDT"
    target_fdv = 1000000000  # $1 billion
    start_time = int(datetime(2025, 4, 1, 15, 0).timestamp() * 1000)  # April 1, 2025, 3:00 PM ET
    end_time = int(datetime(2025, 6, 30, 23, 59).timestamp() * 1000)  # June 30, 2025, 11:59 PM ET
    result = check_fartcoin_fdv(symbol, start_time, end_time, target_fdv)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()