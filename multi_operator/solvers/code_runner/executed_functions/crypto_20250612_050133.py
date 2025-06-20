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

# Binance API URLs
PRIMARY_BINANCE_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def fetch_data_from_binance(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance using the proxy URL first, then falls back to the primary URL if necessary.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data using the proxy URL
        response = requests.get(PROXY_BINANCE_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
        else:
            raise ValueError("No data returned from proxy endpoint.")
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to the primary endpoint if proxy fails
        response = requests.get(PRIMARY_BINANCE_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def get_eth_price_change(symbol, target_datetime):
    """
    Calculates the percentage price change for the ETH/USDT pair for the specified 1-hour candle.
    """
    # Convert target datetime to UTC milliseconds
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds

    # Fetch the data
    data = fetch_data_from_binance(symbol, "1h", start_time, end_time)
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change_percent = ((close_price - open_price) / open_price) * 100
        return price_change_percent
    else:
        raise Exception("Failed to fetch or parse data.")

def main():
    """
    Main function to determine if the price of ETH/USDT went up or down at the specified time.
    """
    # Define the target date and time
    target_datetime = datetime(2025, 6, 12, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    symbol = "ETHUSDT"

    try:
        price_change_percent = get_eth_price_change(symbol, target_datetime)
        logger.info(f"Price change percentage: {price_change_percent}%")

        # Determine the resolution based on the price change
        if price_change_percent >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        logger.error(f"Error processing the price data: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    main()