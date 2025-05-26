import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
SPORTS_DATA_IO_MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
SPORTS_DATA_IO_NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
SPORTS_DATA_IO_NFL_API_KEY = os.getenv("SPORTS_DATA_IO_NFL_API_KEY")
SPORTS_DATA_IO_NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
SPORTS_DATA_IO_CFB_API_KEY = os.getenv("SPORTS_DATA_IO_CFB_API_KEY")
SPORTS_DATA_IO_CBB_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Function to make API requests
def make_request(url, headers, proxy_url=None):
    try:
        response = requests.get(proxy_url if proxy_url else url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if proxy_url:
            logger.warning(f"Proxy failed, trying primary endpoint: {url}")
            return make_request(url, headers)
        else:
            logger.error(f"HTTP error occurred: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
    return None

# Example function to use Binance API
def get_binance_data():
    url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    headers = {"X-MBX-APIKEY": BINANCE_API_KEY}
    data = make_request(url, headers, proxy_url)
    if data:
        logger.info(f"Current BTC/USDT price: {data['price']}")
    else:
        logger.error("Failed to retrieve data from Binance")

# Example function to use Sports Data IO API (MLB)
def get_mlb_data():
    url = "https://api.sportsdata.io/v3/mlb/scores/json/Teams"
    headers = {"Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_MLB_API_KEY}
    teams = make_request(url, headers)
    if teams:
        logger.info(f"Number of MLB teams: {len(teams)}")
    else:
        logger.error("Failed to retrieve MLB data")

# Main function to run examples
if __name__ == "__main__":
    get_binance_data()
    get_mlb_data()