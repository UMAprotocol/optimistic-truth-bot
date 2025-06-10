import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Define the API endpoints
PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_URL = "https://api.binance.com/api/v3"

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from the Binance API using a proxy and falls back to the primary endpoint if necessary.
    
    Args:
        symbol (str): The trading pair symbol.
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    
    Returns:
        float: The lowest price within the given time frame or None if data could not be fetched.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Maximum number of candles
        "startTime": start_time,
        "endTime": end_time
    }

    try:
        # Try fetching data using the proxy endpoint
        response = requests.get(PROXY_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            # Find the lowest price in the returned candles
            return min(float(candle[3]) for candle in data)  # Index 3 is the low price in each candle
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(f"{PRIMARY_URL}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return min(float(candle[3]) for candle in data)
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def check_hyperliquid_dip_to_12():
    """
    Checks if the price of Hyperliquid (HYPE/USDC) dipped to $12 or lower between May 7, 2025, 16:00 and May 31, 2025, 23:59 ET.
    
    Returns:
        str: 'p1' if the price never dipped to $12 or lower, 'p2' if it did, 'p4' if data could not be fetched.
    """
    symbol = "HYPEUSDC"
    start_time = datetime(2025, 5, 7, 16, 0, tzinfo=pytz.timezone("US/Eastern"))
    end_time = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone("US/Eastern"))
    start_time_utc = int(start_time.astimezone(pytz.utc).timestamp() * 1000)
    end_time_utc = int(end_time.astimezone(pytz.utc).timestamp() * 1000)

    lowest_price = fetch_price_data(symbol, start_time_utc, end_time_utc)
    if lowest_price is None:
        return "p4"  # Unable to fetch data
    elif lowest_price <= 12.0:
        return "p2"  # Yes, price dipped to $12 or lower
    else:
        return "p1"  # No, price did not dip to $12 or lower

# Run the check and print the recommendation
recommendation = check_hyperliquid_dip_to_12()
print(f"recommendation: {recommendation}")