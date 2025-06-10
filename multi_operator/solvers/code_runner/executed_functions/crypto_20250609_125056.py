import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
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
        # Try fetching data from the proxy endpoint first
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        logging.warning(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            logging.error(f"Primary endpoint also failed: {e}")
            raise

def resolve_market(symbol, target_date):
    """
    Resolves the market based on the price change of the BTC/USDT pair on Binance.
    """
    # Convert target date to the correct timestamp for the API call
    tz = pytz.timezone("US/Eastern")
    dt_start = tz.localize(datetime.strptime(target_date, "%Y-%m-%d %H:%M"))
    dt_end = dt_start + timedelta(hours=1)
    
    start_time = int(dt_start.timestamp() * 1000)  # Convert to milliseconds
    end_time = int(dt_end.timestamp() * 1000)  # Convert to milliseconds
    
    # Fetch the candle data for the specified hour
    candle_data = fetch_binance_data(symbol, "1h", start_time, end_time)
    
    if candle_data:
        open_price = float(candle_data[1])
        close_price = float(candle_data[4])
        
        # Determine if the price went up or down
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50 if no data

def main():
    """
    Main function to handle the resolution of the market.
    """
    try:
        result = resolve_market("BTCUSDT", "2025-05-28 23:00")
        print(result)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print("recommendation: p3")  # Unknown/50-50 if error occurs

if __name__ == "__main__":
    main()