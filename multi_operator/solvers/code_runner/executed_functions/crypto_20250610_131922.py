import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, start_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
    
    Args:
        symbol (str): The symbol to fetch data for, e.g., 'BTCUSDT'.
        start_time (int): Start time in milliseconds for the data.
    
    Returns:
        float: The closing price of the symbol at the specified time.
    """
    params = {
        "symbol": symbol,
        "interval": "1h",
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later
    }
    
    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Closing price
    except Exception as e:
        print(f"Proxy failed with error: {e}, trying primary API.")
        # Fallback to the primary API endpoint
        try:
            response = requests.get(PRIMARY_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            return float(data[0][4])  # Closing price
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
            raise

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price change of a cryptocurrency.
    
    Args:
        symbol (str): The cryptocurrency symbol, e.g., 'BTCUSDT'.
        target_datetime (datetime): The datetime for which to check the price.
    
    Returns:
        str: 'recommendation: p1' for Down, 'recommendation: p2' for Up.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    
    # Fetch the closing price at the specified time
    closing_price_start = fetch_price_data(symbol, start_time)
    closing_price_end = fetch_price_data(symbol, start_time + 3600000)  # 1 hour later
    
    # Determine if the price went up or down
    if closing_price_end >= closing_price_start:
        return "recommendation: p2"  # Up
    else:
        return "recommendation: p1"  # Down

def main():
    # Example usage
    target_datetime = datetime(2025, 6, 10, 7, 0)  # June 10, 2025, 7:00 AM ET
    result = resolve_market("BTCUSDT", target_datetime)
    print(result)

if __name__ == "__main__":
    main()