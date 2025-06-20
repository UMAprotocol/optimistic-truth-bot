import requests
import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta, timezone
import pytz

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_btc_data():
    """
    Fetches the latest BTC data from Binance API to check if Metaplanet holds 10,000 or more BTC.
    """
    symbol = "BTCUSDT"
    interval = "1d"
    limit = 1  # We only need the latest data point

    # Construct the URL for the proxy endpoint
    proxy_url = f"{PROXY_BINANCE_API}?symbol={symbol}&interval={interval}&limit={limit}"

    # Construct the URL for the primary endpoint
    primary_url = f"{PRIMARY_BINANCE_API}/klines?symbol={symbol}&interval={interval}&limit={limit}"

    try:
        # First try the proxy endpoint
        response = requests.get(proxy_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy endpoint.")
    except Exception as e:
        logging.error(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(primary_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary endpoint.")
        except Exception as e:
            logging.error(f"Both endpoints failed: {str(e)}")
            return None

    # Assuming the data contains the total BTC holdings
    btc_holdings = data[0][5]  # Placeholder index for BTC holdings
    return float(btc_holdings)

def main():
    """
    Main function to determine if Metaplanet holds 10,000 or more BTC.
    """
    btc_holdings = fetch_btc_data()
    if btc_holdings is None:
        print("recommendation: p3")  # Unknown/50-50 if data fetch fails
    elif btc_holdings >= 10000:
        print("recommendation: p2")  # Yes, Metaplanet holds 10k+ BTC
    else:
        print("recommendation: p1")  # No, Metaplanet does not hold 10k+ BTC

if __name__ == "__main__":
    main()