import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API configuration for Binance
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PRIMARY_BINANCE_ENDPOINT = "https://api.binance.com/api/v3"
PROXY_BINANCE_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_from_binance(symbol, start_time, end_time):
    """
    Fetches the price of a cryptocurrency from Binance using a proxy and falls back to the primary endpoint if necessary.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching from the proxy endpoint first
        response = requests.get(f"{PROXY_BINANCE_ENDPOINT}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][2])  # High price in the candle
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{PRIMARY_BINANCE_ENDPOINT}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][2])  # High price in the candle

def check_fartcoin_price():
    """
    Checks if the Fartcoin price reached $3.00 or higher between May 7, 2025, 15:00 and May 31, 2025, 23:59 ET.
    """
    symbol = "FARTCOINSOL"
    start_time = int(datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone("US/Eastern")).timestamp() * 1000)
    end_time = int(datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone("US/Eastern")).timestamp() * 1000)
    
    while start_time < end_time:
        price = fetch_price_from_binance(symbol, start_time, start_time + 60000)  # Check each minute
        if price and price >= 3.00:
            return "recommendation: p2"  # Yes, price reached $3.00 or higher
        start_time += 60000  # Move to the next minute
    
    return "recommendation: p1"  # No, price did not reach $3.00

def main():
    result = check_fartcoin_price()
    print(result)

if __name__ == "__main__":
    main()