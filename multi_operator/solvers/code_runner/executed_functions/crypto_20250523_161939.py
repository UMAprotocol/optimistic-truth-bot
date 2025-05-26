import requests
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_crypto_price(symbol, date_str, timezone_str="US/Eastern"):
    """
    Fetches the closing price of a cryptocurrency for a specific minute candle on a given date.
    
    Args:
        symbol (str): The symbol of the cryptocurrency to fetch.
        date_str (str): The date in 'YYYY-MM-DD' format.
        timezone_str (str): The timezone string.
    
    Returns:
        float: The closing price of the cryptocurrency.
    """
    # Convert date to the correct timestamp
    tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(date_str + " 12:00", "%Y-%m-%d %H:%M")
    local_datetime = tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    timestamp = int(utc_datetime.timestamp() * 1000)  # Convert to milliseconds

    # Prepare API request parameters
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": timestamp,
        "endTime": timestamp + 60000  # 1 minute later
    }

    # Try fetching data from the proxy endpoint first
    try:
        response = requests.get(f"{PROXY_API_URL}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])  # Closing price is the fifth element in the list
        return close_price
    except Exception as e:
        print(f"Proxy failed, error: {e}. Trying primary endpoint.")
        # Fallback to the primary endpoint if proxy fails
        try:
            response = requests.get(f"{PRIMARY_API_URL}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            close_price = float(data[0][4])
            return close_price
        except Exception as e:
            print(f"Both proxy and primary API requests failed: {e}")
            raise

def main():
    """
    Main function to determine if the price of Fartcoin was above $1.40 on May 23, 2025 at 12:00 ET.
    """
    try:
        close_price = fetch_crypto_price("FARTCOINUSDT", "2025-05-23", "US/Eastern")
        if close_price >= 1.4001:
            print("recommendation: p2")  # Yes, price was above $1.40
        else:
            print("recommendation: p1")  # No, price was not above $1.40
    except Exception as e:
        print(f"Unable to determine the price due to an error: {e}")
        print("recommendation: p3")  # Unknown/50-50 due to error

if __name__ == "__main__":
    main()