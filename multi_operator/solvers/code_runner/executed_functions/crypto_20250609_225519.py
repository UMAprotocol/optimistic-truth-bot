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

def fetch_data_from_binance(symbol, interval, start_time, end_time):
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
    headers = {
        "X-MBX-APIKEY": BINANCE_API_KEY
    }

    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            raise

def get_price_change(symbol, target_date_str, target_hour):
    """
    Determines the price change for a given cryptocurrency symbol at a specific hour on a given date.
    """
    # Convert target date and hour to the correct timestamp
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    target_date = target_date.replace(hour=target_hour, minute=0, second=0, microsecond=0)
    target_date_utc = target_date.astimezone(pytz.utc)

    start_time = int(target_date_utc.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later

    # Fetch data from Binance
    data = fetch_data_from_binance(symbol, "1h", start_time, end_time)

    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change_percentage = ((close_price - open_price) / open_price) * 100

        if price_change_percentage >= 0:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 if no data

def main():
    """
    Main function to determine if the price of BTC/USDT was up or down on June 2, 2025 at 3 AM ET.
    """
    symbol = "BTCUSDT"
    target_date_str = "2025-06-02"
    target_hour = 3  # 3 AM ET, considering ET to UTC conversion if necessary

    try:
        result = get_price_change(symbol, target_date_str, target_hour)
        print(f"recommendation: {result}")
    except Exception as e:
        print("Failed to fetch or process data:", e)
        print("recommendation: p3")  # Default to unknown if there's an error

if __name__ == "__main__":
    main()