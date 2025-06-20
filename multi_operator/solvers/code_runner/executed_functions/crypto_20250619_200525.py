import requests
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching from proxy endpoint first
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def get_eth_price_data(date_str, hour):
    """
    Gets the ETH/USDT price data for the specified date and hour.
    """
    # Convert date and hour to the correct timestamp
    dt = datetime.strptime(f"{date_str} {hour}:00:00", "%Y-%m-%d %H:%M:%S")
    dt = pytz.timezone("America/New_York").localize(dt)
    dt_utc = dt.astimezone(pytz.utc)
    start_time = int(dt_utc.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later

    # Fetch data from Binance
    data = fetch_binance_data("ETHUSDT", "1h", start_time, end_time)
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    else:
        raise ValueError("No data returned from Binance API.")

def resolve_market(open_price, close_price):
    """
    Resolves the market based on the open and close prices.
    """
    if close_price >= open_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    """
    Main function to resolve the Ethereum Up or Down market for June 19, 3PM ET.
    """
    try:
        open_price, close_price = get_eth_price_data("2025-06-19", 15)  # 3 PM ET
        resolution = resolve_market(open_price, close_price)
        print(f"recommendation: {resolution}")
    except Exception as e:
        print(f"Error occurred: {e}")
        print("recommendation: p3")  # Unknown/50-50 if an error occurs

if __name__ == "__main__":
    main()