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
            return data[0][4]  # Close price of the candle
    except Exception as e:
        print(f"Proxy failed with error: {e}, falling back to primary endpoint.")
        # Fallback to the primary endpoint
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0][4]  # Close price of the candle
        except Exception as e:
            print(f"Primary endpoint also failed with error: {e}")
            return None

def resolve_market(symbol, target_date, target_hour):
    """
    Resolves the market based on the price change of the BTC/USDT pair.
    """
    # Convert target time to UTC
    eastern = pytz.timezone('US/Eastern')
    naive_dt = datetime.strptime(f"{target_date} {target_hour}:00:00", "%Y-%m-%d %H:%M:%S")
    local_dt = eastern.localize(naive_dt)
    utc_dt = local_dt.astimezone(pytz.utc)

    # Calculate start and end times in milliseconds
    start_time = int(utc_dt.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch close prices at the start and end of the hour
    start_price = fetch_price_data(symbol, "1h", start_time, start_time + 60000)
    end_price = fetch_price_data(symbol, "1h", end_time - 60000, end_time)

    if start_price is None or end_price is None:
        print("recommendation: p4")
        return

    start_price = float(start_price)
    end_price = float(end_price)

    # Determine if the price went up or down
    if end_price >= start_price:
        print("recommendation: p2")  # Up
    else:
        print("recommendation: p1")  # Down

def main():
    # Example usage
    resolve_market("BTCUSDT", "2025-06-09", "16")

if __name__ == "__main__":
    main()