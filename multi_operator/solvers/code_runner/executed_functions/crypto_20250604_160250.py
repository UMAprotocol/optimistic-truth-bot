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
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching from proxy first
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logging.warning(f"Proxy failed with error: {e}. Trying primary endpoint.")
        try:
            # Fallback to primary endpoint
            response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logging.error(f"Primary endpoint also failed with error: {e}.")
            raise

def resolve_market(symbol, target_date, target_time):
    """
    Resolves the market based on the price change of the symbol at the specified time.
    """
    # Convert target time to UTC
    eastern = pytz.timezone('US/Eastern')
    naive_dt = datetime.strptime(f"{target_date} {target_time}", "%Y-%m-%d %H:%M")
    local_dt = eastern.localize(naive_dt)
    utc_dt = local_dt.astimezone(pytz.utc)

    # Calculate start and end times for the 1-hour candle
    start_time = int(utc_dt.timestamp() * 1000)  # Convert to milliseconds
    end_time = int((utc_dt + timedelta(minutes=59)).timestamp() * 1000)  # End time of the 1-hour candle

    # Fetch data
    data = fetch_binance_data(symbol, "1h", start_time, end_time)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change = (close_price - open_price) / open_price * 100

        # Determine resolution based on price change
        if price_change >= 0:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50 if no data

def main():
    # Example usage
    symbol = "BTCUSDT"
    target_date = "2025-06-02"
    target_time = "08:00"
    result = resolve_market(symbol, target_date, target_time)
    print(result)

if __name__ == "__main__":
    main()