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

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy failed with error: {e}, trying primary API endpoint.")
        # Fallback to the primary API endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
            return None

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price change of the cryptocurrency.
    """
    # Convert target datetime to UTC milliseconds
    target_time_utc = int(target_datetime.timestamp() * 1000)
    
    # Fetch price data for the specified time
    data = fetch_price_data(symbol, "1h", target_time_utc, target_time_utc + 3600000)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change = close_price - open_price
        
        if price_change >= 0:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50 if no data available

def main():
    # Define the symbol and the specific time for the market resolution
    symbol = "ETHUSDT"
    target_datetime_str = "2025-06-13 19:00:00"
    timezone_str = "US/Eastern"
    
    # Convert string to datetime object in the specified timezone
    timezone = pytz.timezone(timezone_str)
    target_datetime = datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S")
    target_datetime = timezone.localize(target_datetime)
    
    # Resolve the market
    result = resolve_market(symbol, target_datetime)
    print(result)

if __name__ == "__main__":
    main()