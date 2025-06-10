import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API endpoints
PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_URL = "https://api.binance.com/api/v3"

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from Binance API using a proxy and falls back to the primary endpoint if necessary.
    
    Args:
        symbol (str): The symbol to fetch data for.
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    
    Returns:
        float: The highest price found in the given time range or None if no data is available.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Maximum allowed by Binance
        "startTime": start_time,
        "endTime": end_time
    }

    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            # Extract the highest price from the 'High' value in each candle
            return max(float(candle[2]) for candle in data)
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(f"{PRIMARY_URL}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return max(float(candle[2]) for candle in data)
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def check_fartcoin_price_threshold():
    """
    Checks if Fartcoin reached $1.80 at any point between May 7, 2025, 15:00 and May 31, 2025, 23:59 ET.
    
    Returns:
        str: 'p1' if Fartcoin did not reach $1.80, 'p2' if it did, 'p4' if data could not be fetched.
    """
    symbol = "FARTCOINSOL"
    start_time = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone("US/Eastern"))
    end_time = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone("US/Eastern"))
    start_time_utc = int(start_time.astimezone(pytz.utc).timestamp() * 1000)
    end_time_utc = int(end_time.astimezone(pytz.utc).timestamp() * 1000)

    highest_price = fetch_price_data(symbol, start_time_utc, end_time_utc)
    if highest_price is None:
        return "p4"  # Unable to fetch data
    elif highest_price >= 1.80:
        return "p2"  # Yes, Fartcoin reached $1.80
    else:
        return "p1"  # No, Fartcoin did not reach $1.80

# Main execution
if __name__ == "__main__":
    result = check_fartcoin_price_threshold()
    print(f"recommendation: {result}")