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
    Fetch the closing price of a cryptocurrency at a specific time using Binance API.
    Args:
        symbol (str): The symbol of the cryptocurrency, e.g., 'BTCUSDT'.
        time (datetime): The datetime object representing the specific time.
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
        close_price = float(data[0][4])
        return close_price
    except Exception as e:
        print(f"Proxy failed with error: {e}. Trying primary API.")
        # Fallback to the primary API endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price

def main():
    # Specific date and time for the query
    target_time = datetime.strptime("2025-06-08 14:30", "%Y-%m-%d %H:%M")
    symbol = "BTCUSDT"
    threshold_price = 225000

    try:
        # Fetch the closing price from Binance
        closing_price = fetch_price_from_binance(symbol, target_time)
        print(f"Closing price for {symbol} at {target_time} was {closing_price}")

        # Determine the resolution based on the fetched price
        if closing_price >= threshold_price:
            print("recommendation: p2")  # Yes, price is above or equal to 225,000 USDT
        else:
            print("recommendation: p1")  # No, price is below 225,000 USDT
    except Exception as e:
        print(f"An error occurred: {e}")
        print("recommendation: p4")  # Unable to resolve due to an error

if __name__ == "__main__":
    main()