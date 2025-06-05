import requests
import logging
from datetime import datetime
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_binance_price(symbol, start_time, end_time, proxy_url, primary_url):
    """
    Fetches the closing price of a cryptocurrency from Binance using the provided time range.
    Args:
        symbol (str): The symbol for the crypto pair (e.g., 'ETHUSDT').
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
        proxy_url (str): URL of the proxy endpoint.
        primary_url (str): URL of the primary API endpoint.
    Returns:
        float: The closing price of the cryptocurrency.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Close price
    except Exception as e:
        logging.warning(f"Proxy failed with error {e}, trying primary endpoint.")
        # Fallback to primary endpoint
        response = requests.get(f"{primary_url}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Close price

def resolve_market():
    """
    Resolves the market based on the Ethereum price movement in May 2025.
    """
    symbol = "ETHUSDT"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3"
    
    # Convert dates to milliseconds
    tz = pytz.timezone("US/Eastern")
    start_time = tz.localize(datetime(2025, 5, 1, 12, 0)).timestamp() * 1000
    end_time = tz.localize(datetime(2025, 5, 31, 23, 59)).timestamp() * 1000
    
    try:
        start_price = get_binance_price(symbol, start_time, start_time + 60000, proxy_url, primary_url)
        end_price = get_binance_price(symbol, end_time, end_time + 60000, proxy_url, primary_url)
        
        if start_price < end_price:
            result = "p2"  # Up
        elif start_price > end_price:
            result = "p1"  # Down
        else:
            result = "p3"  # 50-50
    except Exception as e:
        logging.error(f"Failed to resolve market due to error: {e}")
        result = "p4"  # Unable to resolve
    
    return result

if __name__ == "__main__":
    recommendation = resolve_market()
    print(f"recommendation: {recommendation}")