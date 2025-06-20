import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
SPORTS_DATA_IO_NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants for API endpoints
ESPN_API_URL = "https://site.api.espn.com/apis/site/v2/sports/mma/ufc/scoreboard"
SPORTS_DATA_IO_NBA_ENDPOINT = "https://api.sportsdata.io/v3/nba"

def fetch_fight_result(fight_date, fighter1, fighter2):
    """
    Fetches the result of a UFC fight from ESPN API.
    
    Args:
        fight_date (str): Date of the fight in YYYY-MM-DD format.
        fighter1 (str): Name of the first fighter.
        fighter2 (str): Name of the second fighter.
    
    Returns:
        str: 'p1' if fighter1 wins, 'p2' if fighter2 wins, 'p3' for draw or other outcomes.
    """
    try:
        response = requests.get(ESPN_API_URL, params={"dates": fight_date})
        response.raise_for_status()
        data = response.json()
        
        for event in data.get('events', []):
            competitors = event.get('competitions', [{}])[0].get('competitors', [])
            for competitor in competitors:
                if competitor.get('athlete').get('displayName') in [fighter1, fighter2]:
                    winner = competitor.get('winner')
                    if winner:
                        if competitor.get('athlete').get('displayName') == fighter1:
                            return 'p1'
                        elif competitor.get('athlete').get('displayName') == fighter2:
                            return 'p2'
        return 'p3'  # Draw or no clear result
    except requests.RequestException as e:
        print(f"Failed to fetch data: {e}")
        return 'p3'  # Assume draw or unresolved if there is an error

def main():
    # UFC Fight Night: Bellato vs. Craig, scheduled for June 14, 2025
    fight_date = "2025-06-14"
    fighter1 = "Rodolfo Bellato"
    fighter2 = "Paul Craig"
    
    result = fetch_fight_result(fight_date, fighter1, fighter2)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()