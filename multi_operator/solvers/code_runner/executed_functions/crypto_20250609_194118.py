import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_data_from_binance(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1000  # Adjust based on the maximum number of results needed
    }
    
    try:
        # Try fetching from proxy first
        response = requests.get(PROXY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
        else:
            raise ValueError("No data returned from proxy.")
    except Exception as e:
        print(f"Proxy failed with error: {e}. Trying primary API.")
        try:
            # Fallback to primary API
            response = requests.get(PRIMARY_API_URL, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Primary API also failed with error: {e}.")
            return None

def analyze_prices(data):
    """
    Analyzes the fetched price data to determine if a new all-time high was reached.
    """
    if not data:
        return "p4"  # Unable to resolve due to data fetch failure

    highest_price = max([float(candle[2]) for candle in data])  # High price is at index 2
    return "p2" if highest_price > previous_all_time_high else "p1"

def main():
    # Define the symbol and the time range for the query
    symbol = "SOLUSDT"
    start_time = int(datetime(2025, 5, 1).timestamp() * 1000)  # May 1, 2025
    end_time = int(datetime(2025, 5, 31, 23, 59, 59).timestamp() * 1000)  # May 31, 2025

    # Previous all-time high (example value, should be fetched or defined based on actual data)
    global previous_all_time_high
    previous_all_time_high = 250.0  # This should be dynamically determined from historical data

    # Fetch data
    data = fetch_data_from_binance(symbol, start_time, end_time)

    # Analyze data
    recommendation = analyze_prices(data)
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()