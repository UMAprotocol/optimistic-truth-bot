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
        symbol (str): The symbol of the cryptocurrency, e.g., 'BTCUSDT'.
        time (datetime): The datetime object representing the specific time.
    
    Returns:
        float: The closing price or None if an error occurs.
    """
    # Convert datetime to milliseconds since epoch
    timestamp = int(time.timestamp() * 1000)

    # Parameters for the API request
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
        print(f"Proxy failed, error: {e}, trying primary API.")

        # Fallback to the primary API if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            if data and len(data) > 0:
                return float(data[0][4])  # Closing price
        except Exception as e:
            print(f"Primary API failed, error: {e}")
            return None

def main():
    # Example date and time for the query
    query_time = datetime.strptime("2025-06-09 09:30", "%Y-%m-%d %H:%M")
    symbol = "BTCUSDT"
    price = fetch_price_from_binance(symbol, query_time)

    # Threshold price to compare against
    threshold_price = 225000

    if price is None:
        print("recommendation: p4")  # Unable to fetch price
    elif price >= threshold_price:
        print("recommendation: p2")  # Yes, price is above or equal to 225,000 USDT
    else:
        print("recommendation: p1")  # No, price is below 225,000 USDT

if __name__ == "__main__":
    main()