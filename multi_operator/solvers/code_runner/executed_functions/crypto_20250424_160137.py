import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price(symbol, date_str, timezone_str="US/Eastern"):
    """
    Fetches the closing price of a cryptocurrency from Binance at a specific time.
    
    Args:
        symbol (str): The symbol of the cryptocurrency (e.g., 'ETHUSDT').
        date_str (str): The date and time in 'YYYY-MM-DD HH:MM' format.
        timezone_str (str): The timezone of the given date and time.
    
    Returns:
        float: The closing price of the cryptocurrency.
    """
    # Convert date_str to UTC timestamp
    local = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    local_datetime = local.localize(naive_datetime, is_dst=None)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    timestamp = int(utc_datetime.timestamp() * 1000)  # Convert to milliseconds

    # Prepare API request parameters
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": timestamp,
        "endTime": timestamp + 60000  # 1 minute later
    }

    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price
    except Exception as e:
        print(f"Proxy failed, error: {e}, trying primary API...")
        # Fallback to the primary API endpoint
        response = requests.get(PRIMARY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price

def resolve_market():
    """
    Resolves the market based on the closing prices of Ethereum on two specific dates.
    """
    # Define the dates and times for price comparison
    date1 = "2025-04-23 12:00"
    date2 = "2025-04-24 12:00"
    symbol = "ETHUSDT"
    timezone_str = "US/Eastern"

    # Fetch prices
    price1 = fetch_price(symbol, date1, timezone_str)
    price2 = fetch_price(symbol, date2, timezone_str)

    # Determine the market resolution
    if price1 < price2:
        print("recommendation: p2")  # Up
    elif price1 > price2:
        print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # 50-50

if __name__ == "__main__":
    resolve_market()