import requests
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching data using the proxy endpoint
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fallback to the primary endpoint if proxy fails
        response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data

def get_close_price(symbol, date_str, timezone_str="US/Eastern"):
    """
    Get the close price for a specific minute candle on Binance.
    """
    tz = pytz.timezone(timezone_str)
    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    dt = tz.localize(dt).astimezone(pytz.utc)
    start_time = int(dt.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later in milliseconds

    data = fetch_binance_data(symbol, "1m", start_time, end_time)
    if data and len(data) > 0:
        return float(data[0][4])  # Close price
    return None

def main():
    """
    Main function to determine if Ethereum price went up or down between two specific times.
    """
    symbol = "ETHUSDT"
    date1 = "2025-06-07 12:00"
    date2 = "2025-06-08 12:00"

    price1 = get_close_price(symbol, date1)
    price2 = get_close_price(symbol, date2)

    if price1 is None or price2 is None:
        print("recommendation: p4")  # Unable to fetch prices
    elif price2 > price1:
        print("recommendation: p2")  # Price went up
    elif price2 < price1:
        print("recommendation: p1")  # Price went down
    else:
        print("recommendation: p3")  # Prices are the same

if __name__ == "__main__":
    main()