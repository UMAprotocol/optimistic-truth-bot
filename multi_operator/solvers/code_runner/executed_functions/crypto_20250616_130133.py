import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, start_time):
    """
    Fetches price data from Binance API using a proxy with a fallback to the primary endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": "1h",
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later in milliseconds
    }

    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0][4]  # Close price of the candle
    except Exception as e:
        print(f"Proxy failed, error: {e}, trying primary API...")
        try:
            # Fallback to the primary API endpoint
            response = requests.get(PRIMARY_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0][4]  # Close price of the candle
        except Exception as e:
            print(f"Primary API also failed, error: {e}")
            return None

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price change of the cryptocurrency.
    """
    # Convert datetime to UTC timestamp in milliseconds
    utc_datetime = target_datetime.astimezone(pytz.utc)
    start_time = int(utc_datetime.timestamp() * 1000)

    # Fetch the closing price of the target hour
    closing_price = fetch_price_data(symbol, start_time)

    if closing_price is None:
        return "recommendation: p4"  # Unable to fetch data

    # Compare the closing price with the opening price to determine the market resolution
    if float(closing_price) >= 0:
        return "recommendation: p2"  # Price went up
    else:
        return "recommendation: p1"  # Price went down

def main():
    # Define the symbol and the specific date and time for the market
    symbol = "BTCUSDT"
    target_datetime = datetime(2025, 6, 16, 8, 0, tzinfo=pytz.timezone("US/Eastern"))

    # Resolve the market based on the price data
    result = resolve_market(symbol, target_datetime)
    print(result)

if __name__ == "__main__":
    main()