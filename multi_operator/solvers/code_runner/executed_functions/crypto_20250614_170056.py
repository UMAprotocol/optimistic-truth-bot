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
    headers = {
        "X-MBX-APIKEY": BINANCE_API_KEY
    }

    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        print(f"Proxy failed with error: {e}, falling back to primary API.")
        # Fallback to the primary API endpoint
        try:
            response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
            return None

def resolve_market(symbol, target_date_str, target_hour):
    """
    Resolves the market based on the price change of the symbol at the specified date and hour.
    """
    # Convert target date and hour to the correct timestamp
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    target_date = pytz.timezone("US/Eastern").localize(target_date.replace(hour=target_hour))

    # Convert to UTC and milliseconds for the API call
    target_date_utc = target_date.astimezone(pytz.utc)
    start_time = int(target_date_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch price data for the start and end of the period
    start_data = fetch_price_data(symbol, "1h", start_time, start_time + 60000)  # 1 minute after start
    end_data = fetch_price_data(symbol, "1h", end_time, end_time + 60000)  # 1 minute after end

    if start_data and end_data:
        start_price = float(start_data[1])  # Open price
        end_price = float(end_data[4])  # Close price

        if end_price >= start_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50 if data is missing

def main():
    # Example usage
    result = resolve_market("BTCUSDT", "2025-06-14", 12)
    print(result)

if __name__ == "__main__":
    main()