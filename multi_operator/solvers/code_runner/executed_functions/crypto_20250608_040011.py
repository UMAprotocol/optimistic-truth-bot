import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
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
        # Try fetching data from the proxy API first
        response = requests.get(f"{PROXY_API}?symbol={symbol}&interval={interval}&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy API.")
        return data
    except Exception as e:
        logging.warning(f"Proxy API failed: {e}. Attempting primary API.")
        # Fallback to the primary API if proxy fails
        response = requests.get(f"{PRIMARY_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from primary API.")
        return data

def resolve_market(symbol, target_date_str, target_hour):
    """
    Resolves the market based on the price change of the BTC/USDT pair.
    """
    # Convert target time to UTC
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    target_date = pytz.timezone("US/Eastern").localize(datetime(target_date.year, target_date.month, target_date.day, target_hour, 0, 0))
    target_date_utc = target_date.astimezone(pytz.utc)
    
    start_time = int(target_date_utc.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later
    
    # Fetch price data
    data = fetch_price_data(symbol, "1h", start_time, end_time)
    
    if not data or len(data) == 0:
        logging.error("No data available for the specified time.")
        return "recommendation: p4"
    
    # Calculate percentage change
    open_price = float(data[0][1])
    close_price = float(data[0][4])
    change_percentage = ((close_price - open_price) / open_price) * 100
    
    # Determine resolution based on the change
    if change_percentage >= 0:
        return "recommendation: p2"  # Up
    else:
        return "recommendation: p1"  # Down

def main():
    """
    Main function to execute the market resolution logic.
    """
    symbol = "BTCUSDT"
    target_date_str = "2025-06-07"
    target_hour = 23  # 11 PM ET
    
    result = resolve_market(symbol, target_date_str, target_hour)
    print(result)

if __name__ == "__main__":
    main()