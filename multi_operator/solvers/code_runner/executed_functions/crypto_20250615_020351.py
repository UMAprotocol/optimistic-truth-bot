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

# Constants for API endpoints
ESPN_API_URL = "https://site.api.espn.com/apis/site/v2/sports/mma/ufc/scoreboard"

def fetch_ufc_match_result(fighter1, fighter2, event_date):
    """
    Fetches the result of a UFC match between two fighters on a specific date from ESPN API.
    
    Args:
        fighter1 (str): Name of the first fighter.
        fighter2 (str): Name of the second fighter.
        event_date (str): Date of the event in YYYYMMDD format.
    
    Returns:
        str: 'p1' if fighter1 wins, 'p2' if fighter2 wins, 'p3' for draw or other outcomes.
    """
    try:
        response = requests.get(ESPN_API_URL, params={"dates": event_date})
        response.raise_for_status()
        data = response.json()
        
        for event in data.get('events', []):
            competitors = event.get('competitions', [])[0].get('competitors', [])
            if any(fighter1 in competitor.get('athlete').get('displayName') for competitor in competitors) and \
               any(fighter2 in competitor.get('athlete').get('displayName') for competitor in competitors):
                winner = next((competitor for competitor in competitors if competitor.get('winner')), None)
                if winner:
                    if fighter1 in winner.get('athlete').get('displayName'):
                        return 'p1'
                    elif fighter2 in winner.get('athlete').get('displayName'):
                        return 'p2'
                break
        return 'p3'  # Draw or no clear winner
    except Exception as e:
        logging.error(f"Failed to fetch or parse data: {e}")
        return 'p3'  # Default to draw or other outcome in case of error

def main():
    # Example usage
    result = fetch_ufc_match_result("Rodolfo Bellato", "Paul Craig", "20250517")
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()