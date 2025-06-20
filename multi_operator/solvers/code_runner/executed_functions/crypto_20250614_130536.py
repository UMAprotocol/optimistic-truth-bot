import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API = "https://api.binance.com/api/v3"
PROXY_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, interval, start_time):
    """
    Fetches price data from Binance using the proxy API with a fallback to the primary API.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later
    }
    
    try:
        # Try fetching data from the proxy API
        response = requests.get(f"{PROXY_API}?symbol={symbol}&interval={interval}&limit=1&startTime={start_time}&endTime={start_time + 3600000}", timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Proxy API failed: {e}, falling back to primary API")
        # Fallback to the primary API
        response = requests.get(f"{PRIMARY_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the price change of the symbol at the specified target time.
    """
    # Convert target time to milliseconds since epoch
    target_time_ms = int(target_time.timestamp() * 1000)
    
    # Fetch price data
    data = fetch_price_data(symbol, "1h", target_time_ms)
    
    if not data or len(data) < 1:
        return "recommendation: p4"  # Unable to resolve
    
    # Extract the opening and closing prices from the data
    open_price = float(data[0][1])
    close_price = float(data[0][4])
    
    # Determine if the price went up or down
    if close_price >= open_price:
        return "recommendation: p2"  # Up
    else:
        return "recommendation: p1"  # Down

def main():
    # Define the symbol and the specific time for the market resolution
    symbol = "BTCUSDT"
    target_time = datetime(2025, 6, 14, 8, 0)  # June 14, 2025, 8:00 AM ET
    
    # Resolve the market
    result = resolve_market(symbol, target_time)
    print(result)

if __name__ == "__main__":
    main()