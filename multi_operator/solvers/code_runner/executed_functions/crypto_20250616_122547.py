import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Binance API endpoints
PRIMARY_BINANCE_ENDPOINT = "https://api.binance.com/api/v3"
PROXY_BINANCE_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_btc_transactions(start_time, end_time):
    """
    Fetches BTC transactions from Binance API within a specified time range.
    Args:
        start_time (int): Start time in milliseconds since epoch.
        end_time (int): End time in milliseconds since epoch.
    Returns:
        float: Total BTC purchased if data is available, otherwise None.
    """
    url = f"{PROXY_BINANCE_ENDPOINT}/trades"
    params = {
        "symbol": "BTCUSDT",
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1000  # Adjust based on the expected volume of trades
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        trades = response.json()
        total_btc = sum(float(trade['qty']) for trade in trades)
        return total_btc
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch data from proxy endpoint: {e}")
        # Fallback to primary endpoint
        url = f"{PRIMARY_BINANCE_ENDPOINT}/trades"
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            trades = response.json()
            total_btc = sum(float(trade['qty']) for trade in trades)
            return total_btc
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch data from primary endpoint: {e}")
            return None

def resolve_market():
    """
    Resolves the market based on MicroStrategy's BTC purchases between June 10 and June 16, 2025.
    """
    # Define the time range
    start_date = datetime(2025, 6, 10, 0, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 6, 16, 23, 59, 59, tzinfo=pytz.timezone('US/Eastern'))
    start_time_ms = int(start_date.timestamp() * 1000)
    end_time_ms = int(end_date.timestamp() * 1000)

    # Fetch total BTC purchased by MicroStrategy in the defined period
    total_btc_purchased = fetch_btc_transactions(start_time_ms, end_time_ms)

    # Determine the resolution based on the total BTC purchased
    if total_btc_purchased is None:
        print("recommendation: p3")  # Unknown/50-50 if data fetching failed
    elif total_btc_purchased >= 8001:
        print("recommendation: p2")  # Yes, if MicroStrategy purchased 8001 BTC or more
    else:
        print("recommendation: p1")  # No, if MicroStrategy purchased less than 8001 BTC

if __name__ == "__main__":
    resolve_market()