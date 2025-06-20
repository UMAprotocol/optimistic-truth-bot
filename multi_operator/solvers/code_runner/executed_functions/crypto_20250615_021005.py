import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
SPORTS_DATA_IO_CBB_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def fetch_fight_result():
    """
    Fetches the result of the UFC fight between Rodolfo Bellato and Paul Craig.
    """
    # Endpoint and API key for the sports data
    endpoint = "https://api.sportsdata.io/v3/cbb/scores/json/GamesByDate/2025-06-14"
    headers = {
        "Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_CBB_API_KEY
    }

    try:
        # Make the request to the sports data API
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        games = response.json()

        # Search for the specific fight in the data
        for game in games:
            if "Bellato" in game['HomeTeam'] and "Craig" in game['AwayTeam']:
                if game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "Bellato"
                elif game['HomeTeamScore'] < game['AwayTeamScore']:
                    return "Craig"
                else:
                    return "Draw"

        # If no specific match is found, assume it was not scored or postponed
        return "Unknown"

    except requests.RequestException as e:
        logger.error(f"Failed to fetch data: {e}")
        return "Error"

def main():
    """
    Main function to process the UFC fight result and determine the market resolution.
    """
    result = fetch_fight_result()
    if result == "Bellato":
        print("recommendation: p2")
    elif result == "Craig":
        print("recommendation: p1")
    elif result == "Draw":
        print("recommendation: p3")
    else:
        print("recommendation: p3")

if __name__ == "__main__":
    main()