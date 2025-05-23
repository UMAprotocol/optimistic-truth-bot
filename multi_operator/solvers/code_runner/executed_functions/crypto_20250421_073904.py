import requests
import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
SPORTS_DATA_IO_NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_fight_result():
    """
    Fetches the result of the UFC fight between Evan Elder and Ahmad Hassanzada.
    """
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/2025-04-27"
    headers = {
        'Ocp-Apim-Subscription-Key': SPORTS_DATA_IO_NBA_API_KEY
    }
    
    try:
        # First try the proxy endpoint
        response = requests.get(PROXY_ENDPOINT, headers=headers, timeout=10)
        response.raise_for_status()
        games = response.json()
    except Exception as e:
        logging.info(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        games = response.json()

    # Search for the specific fight result
    for game in games:
        if "Evan Elder" in game['HomeTeam'] or "Ahmad Hassanzada" in game['AwayTeam']:
            if game['Winner'] == "Home":
                return "Elder"
            elif game['Winner'] == "Away":
                return "Hassanzada"
            else:
                return "Draw"

    return "Unknown"

def main():
    """
    Main function to determine the outcome of the UFC fight.
    """
    try:
        result = fetch_fight_result()
        if result == "Elder":
            print("recommendation: p2")
        elif result == "Hassanzada":
            print("recommendation: p1")
        elif result == "Draw":
            print("recommendation: p3")
        else:
            print("recommendation: p3")  # Handle unknown or unresolved cases as 50-50
    except Exception as e:
        logging.error(f"Failed to fetch fight result: {e}")
        print("recommendation: p3")  # Default to 50-50 in case of errors

if __name__ == "__main__":
    main()