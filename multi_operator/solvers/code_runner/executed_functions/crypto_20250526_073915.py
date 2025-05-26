import requests
import os
from datetime import datetime
from pytz import timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3/klines"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price(symbol, date_str, time_str, tz_str):
    # Convert local time to UTC timestamp
    local_tz = timezone(tz_str)
    naive_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    local_datetime = local_tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(timezone('UTC'))
    start_time = int(utc_datetime.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later

    # Function to make API requests
    def make_request(url):
        params = {
            "symbol": symbol,
            "interval": "1m",
            "startTime": start_time,
            "endTime": end_time,
            "limit": 1
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Close price

    # Try proxy endpoint first
    try:
        return make_request(f"{PROXY_ENDPOINT}")
    except Exception as e:
        print(f"Proxy failed: {e}, trying primary endpoint.")
        # Fallback to primary endpoint
        return make_request(f"{PRIMARY_ENDPOINT}")

def main():
    # Define the dates, times, and symbol
    symbol = "ETHUSDT"
    date1 = "2025-05-25"
    date2 = "2025-05-26"
    time = "12:00"
    tz_str = "US/Eastern"

    # Fetch prices
    try:
        price1 = fetch_price(symbol, date1, time, tz_str)
        price2 = fetch_price(symbol, date2, time, tz_str)

        # Determine the resolution
        if price1 < price2:
            recommendation = "p2"  # Up
        elif price1 > price2:
            recommendation = "p1"  # Down
        else:
            recommendation = "p3"  # 50-50
    except Exception as e:
        print(f"Error fetching prices: {e}")
        recommendation = "p4"  # Unknown

    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()