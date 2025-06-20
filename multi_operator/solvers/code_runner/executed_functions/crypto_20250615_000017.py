import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"

def fetch_price_data(symbol, start_time):
    """
    Fetches price data from Binance using a proxy endpoint with a fallback to the primary endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": "1h",
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later in milliseconds
    }
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0][4]  # Close price of the candle
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fallback to the primary endpoint if proxy fails
        try:
            response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0][4]  # Close price of the candle
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
            return None

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the price change of the symbol at the specified target time.
    """
    # Convert target time to milliseconds since epoch
    target_time_ms = int(target_time.timestamp() * 1000)
    
    # Fetch the closing price at the target time
    closing_price_start = fetch_price_data(symbol, target_time_ms)
    closing_price_end = fetch_price_data(symbol, target_time_ms + 3600000)
    
    if closing_price_start and closing_price_end:
        # Calculate the percentage change
        change = ((float(closing_price_end) - float(closing_price_start)) / float(closing_price_start)) * 100
        if change >= 0:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50 due to data fetch failure

def main():
    # Example usage
    symbol = "BTCUSDT"
    target_time = datetime(2025, 6, 14, 19, 0)  # June 14, 2025, 7 PM ET
    result = resolve_market(symbol, target_time)
    print(result)

if __name__ == "__main__":
    main()