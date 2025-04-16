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

def fetch_ufc_result(event_date, fighters):
    """
    Fetches the result of a UFC fight from ESPN or other credible sources.

    Args:
        event_date: Date of the event in YYYY-MM-DD format
        fighters: Tuple containing the names of the fighters (fighter1, fighter2)

    Returns:
        Winner's name or 'Draw' or 'No Contest'
    """
    logger.info(f"Fetching UFC result for {fighters[0]} vs {fighters[1]} on {event_date}")
    
    # Convert the event date to UTC timestamp
    event_datetime = datetime.strptime(event_date, "%Y-%m-%d")
    event_timestamp = int(event_datetime.replace(tzinfo=timezone.utc).timestamp())

    # API endpoint setup
    api_url = "https://site.api.espn.com/apis/site/v2/sports/mma/ufc/scoreboard"
    params = {
        "dates": event_date,
        "apikey": SPORTS_DATA_IO_MLB_API_KEY
    }

    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()

        # Assuming the data structure contains events and competitors
        for event in data.get('events', []):
            for competition in event.get('competitions', []):
                competitors = competition.get('competitors', [])
                if any(fighter['name'] == fighters[0] for fighter in competitors) and \
                   any(fighter['name'] == fighters[1] for fighter in competitors):
                    winner = next((competitor for competitor in competitors if competitor.get('winner', False)), None)
                    if winner:
                        return winner['name']
                    return 'Draw'  # Assuming draw if no winner found

        logger.info("No match found or match not yet scored")
        return 'No Contest'  # Default to no contest if no data found

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch UFC results: {e}")
        return 'No Contest'

def main():
    """
    Main function to handle the UFC fight result query.
    """
    event_date = "2025-04-12"
    fighters = ("Alberto Montes", "Roberto Romero")

    result = fetch_ufc_result(event_date, fighters)

    if result == fighters[0]:
        recommendation = "p2"  # Montes wins
    elif result == fighters[1]:
        recommendation = "p1"  # Romero wins
    else:
        recommendation = "p3"  # Draw or no contest

    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()