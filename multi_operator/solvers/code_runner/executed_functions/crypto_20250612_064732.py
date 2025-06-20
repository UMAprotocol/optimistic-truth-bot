import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_from_binance(symbol, time):
    """
    Fetches the closing price of a cryptocurrency at a specific time using Binance API.
    
    Args:
        symbol (str): The symbol of the cryptocurrency to fetch, e.g., 'BTCUSDT'.
        time (datetime): The datetime object representing the exact time for the price.
    
    Returns:
        float: The closing price of the cryptocurrency.
    """
    # Convert datetime to milliseconds since epoch
    timestamp = int(time.timestamp() * 1000)

    # Parameters for the API call
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": timestamp,
        "endTime": timestamp + 60000  # 1 minute later
    }

    try:
        # Try fetching from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            return float(data[0][4])  # Closing price
    except Exception as e:
        print(f"Proxy failed, trying primary API: {e}")
        # Fallback to the primary API if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            return float(data[0][4])  # Closing price

    raise Exception("Failed to fetch data from both proxy and primary endpoints.")

def main():
    # Example date and time for the query
    query_time = datetime.strptime("2025-06-11 15:30:00", "%Y-%m-%d %H:%M:%S")
    symbol = "BTCUSDT"
    threshold_price = 325000

    try:
        closing_price = fetch_price_from_binance(symbol, query_time)
        print(f"Fetched closing price: {closing_price}")
        if closing_price >= threshold_price:
            print("recommendation: p2")  # Yes, price is above or equal to threshold
        else:
            print("recommendation: p1")  # No, price is below threshold
    except Exception as e:
        print(f"Error fetching price: {e}")
        print("recommendation: p4")  # Unable to resolve due to error

if __name__ == "__main__":
    main()