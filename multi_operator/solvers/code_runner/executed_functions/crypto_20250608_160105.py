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
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def get_price_change(symbol, date_str, hour):
    """
    Calculates the price change for the specified symbol on Binance at the given date and hour.
    """
    # Convert the specified hour in ET to UTC
    et_timezone = pytz.timezone("US/Eastern")
    utc_timezone = pytz.utc
    naive_datetime = datetime.strptime(date_str + f" {hour}:00:00", "%Y-%m-%d %H:%M:%S")
    local_dt = et_timezone.localize(naive_datetime)
    utc_dt = local_dt.astimezone(utc_timezone)

    # Calculate start and end times in milliseconds for the 1-hour candle
    start_time = int(utc_dt.timestamp() * 1000)
    end_time = int((utc_dt + timedelta(hours=1)).timestamp() * 1000)

    # Fetch data from Binance
    data = fetch_binance_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change_percentage = ((close_price - open_price) / open_price) * 100
        return price_change_percentage
    else:
        return None

def main():
    """
    Main function to determine if the price of BTC/USDT went up or down on June 8, 2025 at 11 AM ET.
    """
    symbol = "BTCUSDT"
    date_str = "2025-06-08"
    hour = 11  # 11 AM ET

    price_change_percentage = get_price_change(symbol, date_str, hour)
    if price_change_percentage is not None:
        if price_change_percentage >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 due to data fetch failure

if __name__ == "__main__":
    main()