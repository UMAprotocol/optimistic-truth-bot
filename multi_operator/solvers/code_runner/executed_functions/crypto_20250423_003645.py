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

def fetch_price_from_binance(symbol, start_time, end_time):
    """
    Fetches the highest price of a cryptocurrency from Binance within a given time range.
    Args:
        symbol (str): The symbol of the cryptocurrency to fetch.
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    Returns:
        float: The highest price found, or None if no data could be fetched.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            high_prices = [float(candle[2]) for candle in data]
            return max(high_prices)
    except Exception as e:
        print(f"Proxy failed with error: {e}, trying primary API.")
        # Fallback to the primary API if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            if data:
                high_prices = [float(candle[2]) for candle in data]
                return max(high_prices)
        except Exception as e:
            print(f"Primary API failed with error: {e}")
            return None

def check_solana_price_threshold():
    """
    Checks if the price of Solana (SOLUSDT) reached $150 at any point in April 2025.
    Returns:
        str: Recommendation based on the price check.
    """
    # Define the time range for April 2025 in Eastern Time
    tz = pytz.timezone("US/Eastern")
    start_date = tz.localize(datetime(2025, 4, 1))
    end_date = tz.localize(datetime(2025, 4, 30, 23, 59, 59))
    
    # Convert to UTC and then to milliseconds
    start_time_utc = int(start_date.astimezone(pytz.utc).timestamp() * 1000)
    end_time_utc = int(end_date.astimezone(pytz.utc).timestamp() * 1000)
    
    # Symbol for Solana trading against USDT on Binance
    symbol = "SOLUSDT"
    
    # Fetch the highest price in the given time range
    highest_price = fetch_price_from_binance(symbol, start_time_utc, end_time_utc)
    
    # Determine the recommendation based on the highest price
    if highest_price is not None and highest_price >= 150:
        return "recommendation: p2"  # Yes, it reached $150 or higher
    else:
        return "recommendation: p1"  # No, it did not reach $150

# Run the check and print the result
if __name__ == "__main__":
    result = check_solana_price_threshold()
    print(result)