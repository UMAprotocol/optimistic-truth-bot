import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price(symbol, date_str, timezone_str="US/Eastern"):
    """
    Fetches the closing price of a cryptocurrency for a specific minute candle on Binance.
    
    Args:
        symbol (str): The symbol of the cryptocurrency pair (e.g., 'BTCUSDT').
        date_str (str): The date and time in 'YYYY-MM-DD HH:MM' format.
        timezone_str (str): The timezone of the given date and time.
    
    Returns:
        float: The closing price of the cryptocurrency.
    """
    # Convert date string to UTC timestamp
    local = pytz.timezone(timezone_str)
    naive = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    local_dt = local.localize(naive, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    timestamp = int(utc_dt.timestamp() * 1000)  # Convert to milliseconds

    # Prepare API request parameters
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": timestamp,
        "endTime": timestamp + 60000  # One minute later
    }

    # Try fetching data from the proxy endpoint first
    try:
        response = requests.get(PROXY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price
    except Exception as e:
        print(f"Proxy failed, error: {e}, trying primary API.")
        # Fallback to the primary API if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            close_price = float(data[0][4])
            return close_price
        except Exception as e:
            print(f"Both proxy and primary API requests failed: {e}")
            raise

def main():
    # Define the cryptocurrency and the specific times to check
    symbol = "FARTCOINUSDT"
    date1 = "2025-05-23 12:00"
    date2 = "2025-05-24 12:00"

    try:
        # Fetch prices for both dates
        price1 = fetch_price(symbol, date1)
        price2 = fetch_price(symbol, date2)

        # Determine the market resolution based on the fetched prices
        if price1 < price2:
            print("recommendation: p2")  # Up
        elif price1 > price2:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    except Exception as e:
        print(f"Failed to resolve market due to an error: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()