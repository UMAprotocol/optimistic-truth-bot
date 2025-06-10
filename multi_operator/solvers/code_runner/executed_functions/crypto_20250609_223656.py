import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1000,  # Maximum allowed by Binance
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data using the proxy endpoint
        response = requests.get(f"{PROXY_BINANCE_API}", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def check_bitcoin_dip_to_85k(start_date, end_date):
    """
    Checks if Bitcoin dipped to $85,000 or lower between the given start and end dates.
    """
    # Convert dates to timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))
    
    start_timestamp = int(start_dt.timestamp() * 1000)
    end_timestamp = int(end_dt.timestamp() * 1000)
    
    # Fetch data from Binance
    candles = fetch_binance_data("BTCUSDT", "1m", start_timestamp, end_timestamp)
    
    if candles:
        for candle in candles:
            low_price = float(candle[3])  # Low price is the fourth element in the list
            if low_price <= 85000:
                return True
    return False

def main():
    """
    Main function to determine if Bitcoin dipped to $85k in May 2025.
    """
    result = check_bitcoin_dip_to_85k("2025-05-01", "2025-05-31")
    if result:
        print("recommendation: p2")  # Yes, Bitcoin dipped to $85k or lower
    else:
        print("recommendation: p1")  # No, Bitcoin did not dip to $85k or lower

if __name__ == "__main__":
    main()