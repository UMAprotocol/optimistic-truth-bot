import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from Binance API for a given symbol between start_time and end_time.
    Uses a proxy endpoint with a fallback to the primary endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data using the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fallback to the primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data

def check_solana_price_dip_to_80(start_date, end_date, timezone_str="US/Eastern"):
    """
    Checks if the price of Solana dipped to $80 or below between start_date and end_date.
    """
    # Convert dates to UTC timestamps
    tz = pytz.timezone(timezone_str)
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))
    
    start_time = int(start_dt.timestamp() * 1000)  # Convert to milliseconds
    end_time = int(end_dt.timestamp() * 1000)  # Convert to milliseconds
    
    # Fetch price data
    data = fetch_price_data("SOLUSDT", start_time, end_time)
    
    # Check if any 1-minute candle low price was $80 or below
    for candle in data:
        low_price = float(candle[3])  # Low price is the fourth element in the list
        if low_price <= 80.00:
            return True
    
    return False

def main():
    """
    Main function to determine if Solana dipped to $80 in May 2025.
    """
    result = check_solana_price_dip_to_80("2025-05-01", "2025-05-31")
    if result:
        print("recommendation: p2")  # Yes, Solana dipped to $80 or below
    else:
        print("recommendation: p1")  # No, Solana did not dip to $80 or below

if __name__ == "__main__":
    main()