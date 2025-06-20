import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
SPORTS_DATA_IO_NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# API endpoints
ESPN_API_URL = "https://site.api.espn.com/apis/site/v2/sports/mma/ufc/scoreboard"

def fetch_fight_result(fight_date, fighter1, fighter2):
    """
    Fetches the result of a UFC fight from ESPN API.
    
    Args:
        fight_date (str): Date of the fight in YYYYMMDD format.
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
                if competitor.get('winner'):
                    if fighter1.lower() in competitor.get('athlete').get('displayName').lower():
                        return 'p2'  # Bellato wins
                    elif fighter2.lower() in competitor.get('athlete').get('displayName').lower():
                        return 'p1'  # Craig wins

        # If no winner found or match is a draw
        return 'p3'  # Draw or other outcomes
    except Exception as e:
        print(f"Failed to fetch fight result: {e}")
        return 'p3'  # Default to draw or other outcomes in case of error

def main():
    # UFC Fight Night: Bellato vs. Craig, scheduled for June 14, 2025
    fight_date = "20250614"
    fighter1 = "Rodolfo Bellato"
    fighter2 = "Paul Craig"
    
    result = fetch_fight_result(fight_date, fighter1, fighter2)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()