import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def get_price_change(symbol, start_time):
    """
    Determines if the price of a cryptocurrency has gone up or down based on the closing prices.
    """
    # Convert start time to milliseconds since this is what Binance API expects
    start_time_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    start_time_utc = int(start_time_dt.replace(tzinfo=pytz.utc).timestamp() * 1000)
    end_time_utc = start_time_utc + 3600000  # 1 hour later

    # Fetch price data
    data = fetch_price_data(symbol, "1h", start_time_utc, end_time_utc)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 if no data available

def main():
    """
    Main function to determine if the price of BTC/USDT has gone up or down.
    """
    # Define the symbol and the start time for the 1 hour candle
    symbol = "BTCUSDT"
    start_time = "2025-06-03 09:00:00"  # June 3, 2025, 9 AM ET

    # Convert ET to UTC
    et_timezone = pytz.timezone("US/Eastern")
    naive_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    local_dt = et_timezone.localize(naive_dt)
    utc_dt = local_dt.astimezone(pytz.utc)
    start_time_utc = utc_dt.strftime("%Y-%m-%d %H:%M:%S")

    # Get the price change result
    result = get_price_change(symbol, start_time_utc)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()