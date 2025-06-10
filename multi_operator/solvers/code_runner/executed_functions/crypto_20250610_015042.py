import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_data_from_binance(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1000  # Adjust based on the maximum number of results needed
    }
    
    try:
        # Try fetching from the proxy first
        response = requests.get(PROXY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
        else:
            raise ValueError("No data returned from proxy.")
    except Exception as e:
        print(f"Proxy failed with error: {e}. Trying primary API.")
        # Fallback to the primary API if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params)
        response.raise_for_status()
        return response.json()

def check_ethereum_high_in_may():
    """
    Checks if Ethereum reached a new all-time high in May 2025.
    """
    # Define the time period for May 2025 in UTC
    start_date = datetime(2025, 5, 1, 4, 0, 0, tzinfo=pytz.utc)  # Adjusted for ET to UTC (+4 hours)
    end_date = datetime(2025, 6, 1, 3, 59, 59, tzinfo=pytz.utc)  # Adjusted for ET to UTC (+4 hours)
    
    # Convert datetime to milliseconds since epoch
    start_time = int(start_date.timestamp() * 1000)
    end_time = int(end_date.timestamp() * 1000)
    
    # Fetch data
    data = fetch_data_from_binance("ETHUSDT", start_time, end_time)
    
    # Find the highest price in the data
    highest_price = 0
    for candle in data:
        high_price = float(candle[2])  # High price is at index 2
        if high_price > highest_price:
            highest_price = high_price
    
    # Compare with historical high (this value should be fetched or stored securely)
    historical_high = 4800  # Example value, should be updated with actual historical high before May 2025
    
    if highest_price > historical_high:
        return "recommendation: p2"  # Yes, new all-time high
    else:
        return "recommendation: p1"  # No new all-time high

def main():
    result = check_ethereum_high_in_may()
    print(result)

if __name__ == "__main__":
    main()