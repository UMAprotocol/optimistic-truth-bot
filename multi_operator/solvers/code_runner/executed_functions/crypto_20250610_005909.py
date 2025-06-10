import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# API keys and endpoints
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"

def fetch_data_from_binance(symbol, start_time, end_time):
    """
    Fetches data from Binance using the proxy endpoint with a fallback to the primary endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Maximum allowed by Binance
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data using the proxy endpoint
        response = requests.get(PROXY_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
        else:
            raise ValueError("No data returned from proxy endpoint.")
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def check_solana_price_dip_to_target(start_date, end_date, target_price):
    """
    Checks if the price of Solana dipped to or below the target price within the specified date range.
    """
    # Convert dates to timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))
    
    start_ts = int(start_dt.timestamp() * 1000)
    end_ts = int(end_dt.timestamp() * 1000)
    
    # Fetch data
    data = fetch_data_from_binance("SOLUSDT", start_ts, end_ts)
    
    # Check if any low price in the data dips to or below the target price
    for candle in data:
        low_price = float(candle[3])  # Low price is the fourth element in the list
        if low_price <= target_price:
            return True
    return False

def main():
    """
    Main function to determine if Solana dipped to $130 in May 2025.
    """
    result = check_solana_price_dip_to_target("2025-05-01", "2025-05-31", 130.00)
    if result:
        print("recommendation: p2")  # Yes, it dipped to $130 or lower
    else:
        print("recommendation: p1")  # No, it did not dip to $130 or lower

if __name__ == "__main__":
    main()