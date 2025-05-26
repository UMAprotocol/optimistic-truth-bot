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

# API endpoints
BINANCE_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
SPORTS_DATA_IO_MLB_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json/Teams"

# Headers for Sports Data IO
HEADERS_MLB = {"Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_MLB_API_KEY}

def get_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to retrieve data: {e}")
        return None

def main():
    # Example usage of the MLB API
    mlb_teams = get_data(SPORTS_DATA_IO_MLB_ENDPOINT, HEADERS_MLB)
    if mlb_teams:
        logger.info(f"Number of MLB teams retrieved: {len(mlb_teams)}")
    else:
        logger.info("No MLB teams data could be retrieved.")

    # Example usage of the Binance API
    binance_data = get_data(BINANCE_ENDPOINT, {"X-MBX-APIKEY": BINANCE_API_KEY})
    if binance_data:
        logger.info("Binance data retrieved successfully.")
    else:
        logger.info("Failed to retrieve Binance data.")

if __name__ == "__main__":
    main()