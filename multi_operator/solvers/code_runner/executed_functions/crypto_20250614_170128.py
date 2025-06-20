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
PRIMARY_API_ENDPOINT = "https://api.binance.com/api/v3/klines"
PROXY_API_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy endpoint.
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
        response = requests.get(PROXY_API_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fallback to the primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_ENDPOINT, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
            raise

def get_price_change(symbol, target_datetime):
    """
    Calculates the price change for a specific 1-hour interval.
    """
    # Convert target datetime to UTC timestamp in milliseconds
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch price data
    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return ((close_price - open_price) / open_price) * 100
    else:
        return None

def main():
    """
    Main function to determine if the Bitcoin price went up or down.
    """
    target_date_str = "2025-06-14"
    target_hour = 12  # 12 PM ET
    symbol = "BTCUSDT"
    
    # Convert target time to UTC
    target_time = datetime.strptime(target_date_str, "%Y-%m-%d")
    target_time = target_time.replace(hour=target_hour, minute=0, second=0)
    eastern = pytz.timezone("US/Eastern")
    target_time = eastern.localize(target_time)
    target_time_utc = target_time.astimezone(pytz.utc)

    try:
        price_change = get_price_change(symbol, target_time_utc)
        if price_change is not None:
            if price_change >= 0:
                print("recommendation: p2")  # Up
            else:
                print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # Unknown/50-50
    except Exception as e:
        print(f"Error occurred: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()