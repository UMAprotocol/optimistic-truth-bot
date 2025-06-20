import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables
load_dotenv()

# API keys
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API = "https://api.binance.com/api/v3"
PROXY_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance using the proxy API with a fallback to the primary API.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy API
        response = requests.get(f"{PROXY_API}?symbol={symbol}&interval={interval}&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy API.")
        return data
    except Exception as e:
        logging.warning(f"Proxy API failed: {e}. Attempting primary API.")
        # Fallback to the primary API
        response = requests.get(f"{PRIMARY_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from primary API.")
        return data

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the price change of the ETH/USDT pair at a specific time.
    """
    # Convert target time to UTC milliseconds
    target_datetime = datetime.strptime(target_time, "%Y-%m-%d %H:%M:%S")
    target_timestamp = int(target_datetime.replace(tzinfo=pytz.UTC).timestamp() * 1000)
    
    # Fetch price data for the specified time
    data = fetch_price_data(symbol, "1h", target_timestamp, target_timestamp + 3600000)  # 1 hour in milliseconds
    
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change = (close_price - open_price) / open_price
        
        if price_change >= 0:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50

def main():
    """
    Main function to handle the resolution of the market.
    """
    # Define the symbol and target time based on the market specifics
    symbol = "ETHUSDT"
    target_time = "2025-06-15 10:00:00"  # June 15, 2025, 10 AM ET converted to UTC
    
    # Resolve the market
    result = resolve_market(symbol, target_time)
    print(result)

if __name__ == "__main__":
    main()