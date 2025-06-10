import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try proxy endpoint first
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price

def check_hyperliquid_price():
    """
    Checks if the price of HYPE/USDC dipped to $20 or lower between specified dates.
    """
    symbol = "HYPEUSDC"
    start_date = datetime(2025, 5, 7, 16, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    end_date = datetime(2025, 5, 31, 23, 59, 59, tzinfo=pytz.timezone("US/Eastern"))
    
    # Convert to milliseconds since this is what Binance API expects
    start_time = int(start_date.timestamp() * 1000)
    end_time = int(end_date.timestamp() * 1000)
    
    try:
        price = fetch_price_data(symbol, start_time, end_time)
        if price <= 20.0:
            return "recommendation: p2"  # Yes, it dipped to $20 or lower
        else:
            return "recommendation: p1"  # No, it did not dip to $20 or lower
    except Exception as e:
        print(f"Error fetching price data: {e}")
        return "recommendation: p3"  # Unknown/50-50 due to error

def main():
    result = check_hyperliquid_price()
    print(result)

if __name__ == "__main__":
    main()