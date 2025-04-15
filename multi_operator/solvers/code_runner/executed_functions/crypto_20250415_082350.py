import requests
import logging
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API key for sports data
SPORTS_DATA_IO_MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

def fetch_fight_result(event_date, fighters):
    """
    Fetches the result of a UFC fight from a sports data API.

    Args:
        event_date: Date of the event in YYYY-MM-DD format
        fighters: Tuple containing the names of the fighters (fighter1, fighter2)

    Returns:
        Result of the fight as 'Montes', 'Romero', or 'Draw'
    """
    logger.info(f"Fetching fight result for {fighters[0]} vs {fighters[1]} on {event_date}")
    
    # Construct the API URL
    api_url = f"https://api.sportsdata.io/v3/mma/scores/json/Fight/{event_date}"
    headers = {
        "Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_MLB_API_KEY
    }

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Assuming the API returns a list of fights, we find the relevant fight
        for fight in data:
            if fighters[0] in fight['Fighters'] and fighters[1] in fight['Fighters']:
                if fight['Winner'] == fighters[0]:
                    return 'Montes'
                elif fight['Winner'] == fighters[1]:
                    return 'Romero'
                else:
                    return 'Draw'
        
        logger.error("Fight not found in the data returned.")
        return 'Draw'  # Default to draw if fight not found or no clear winner

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return 'Draw'  # Default to draw in case of API failure

def main():
    """
    Main function to handle the resolution of the UFC fight market.
    """
    event_date = "2025-04-12"
    fighters = ("Alberto Montes", "Roberto Romero")
    
    logger.info("Starting resolution process for UFC fight market.")
    
    try:
        result = fetch_fight_result(event_date, fighters)
        if result == 'Montes':
            print("recommendation: p2")
        elif result == 'Romero':
            print("recommendation: p1")
        else:
            print("recommendation: p3")
    except Exception as e:
        logger.error(f"Error during resolution process: {e}")
        print("recommendation: p3")  # Default to unknown/50-50 in case of any errors

if __name__ == "__main__":
    main()