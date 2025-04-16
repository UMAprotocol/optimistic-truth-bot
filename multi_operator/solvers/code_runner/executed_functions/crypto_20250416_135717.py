import requests
import logging
from datetime import datetime, timezone
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
        Winner's name or 'Draw' or 'No Contest'
    """
    api_url = "https://api.sportsdata.io/v3/mma/scores/json/Schedule/UFC"
    headers = {
        "Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_MLB_API_KEY
    }
    params = {
        "date": event_date
    }

    try:
        response = requests.get(api_url, headers=headers, params=params)
        response.raise_for_status()
        events = response.json()

        for event in events:
            if fighters[0] in event['Fighters'] and fighters[1] in event['Fighters']:
                if event['Status'] == "Finished":
                    return event['Winner']
                elif event['Status'] in ["Canceled", "Postponed"]:
                    return "No Contest"
        return "No Contest"
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return "No Contest"

def main():
    """
    Main function to determine the outcome of the UFC fight between Alberto Montes and Roberto Romero.
    """
    event_date = "2025-04-12"
    fighters = ("Alberto Montes", "Roberto Romero")
    result = fetch_fight_result(event_date, fighters)

    if result == fighters[0]:
        recommendation = "p2"  # Montes wins
    elif result == fighters[1]:
        recommendation = "p1"  # Romero wins
    else:
        recommendation = "p3"  # Draw or No Contest

    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()