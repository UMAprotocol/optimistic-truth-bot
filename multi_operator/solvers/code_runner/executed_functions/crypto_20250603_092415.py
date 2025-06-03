import requests
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

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
    headers = {
        "X-MBX-APIKEY": BINANCE_API_KEY
    }

    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_BINANCE_API, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_BINANCE_API, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            raise

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the close price of the cryptocurrency at the specified time.
    """
    # Convert target time to milliseconds since this is what Binance API expects
    start_time = int(target_time.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later

    # Fetch data
    data = fetch_binance_data(symbol, "1m", start_time, end_time)
    if data:
        close_price = float(data[0][4])  # Close price is the 5th element in the list
        print(f"Close price for {symbol} at {target_time} UTC is {close_price}")
        if close_price >= 200000:
            print("recommendation: p2")  # Yes, price is higher than or equal to 200,000 USDT
        else:
            print("recommendation: p1")  # No, price is lower than 200,000 USDT
    else:
        print("recommendation: p4")  # Unable to fetch data

def main():
    """
    Main function to handle the resolution of the market.
    """
    symbol = "BTCUSDT"
    target_time = datetime(2025, 6, 3, 9, 0, tzinfo=timezone.utc)  # June 3, 2025 at 9:00 UTC
    resolve_market(symbol, target_time)

if __name__ == "__main__":
    main()