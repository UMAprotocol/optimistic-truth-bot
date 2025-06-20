import requests
import logging
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
SPORTS_DATA_IO_CBB_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

def fetch_fight_result():
    """
    Fetches the result of the UFC fight between Rodolfo Bellato and Paul Craig.
    """
    url = "https://api.sportsdata.io/v3/mma/scores/json/Fight/{fight_id}"
    headers = {
        "Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_CBB_API_KEY
    }
    fight_id = "BellatoVsCraig-UFCFightNight"  # This would be the actual ID used in the API

    try:
        response = requests.get(url.format(fight_id=fight_id), headers=headers)
        response.raise_for_status()
        fight_data = response.json()

        winner = fight_data.get("Winner")
        if winner == "Rodolfo Bellato":
            return "p2"  # Bellato wins
        elif winner == "Paul Craig":
            return "p1"  # Craig wins
        else:
            return "p3"  # Draw or no result

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return "p3"  # Resolve as unknown/50-50 if API fails

def main():
    """
    Main function to determine the outcome of the UFC fight.
    """
    result = fetch_fight_result()
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()