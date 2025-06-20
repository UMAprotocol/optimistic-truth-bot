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
NBA_API_URL = "https://api.sportsdata.io/v3/nba"

def fetch_ufc_fight_result(fighter1, fighter2, event_date):
    """
    Fetches the result of a UFC fight from the SportsDataIO NBA API.
    Args:
        fighter1: Name of the first fighter
        fighter2: Name of the second fighter
        event_date: Date of the event in YYYY-MM-DD format
    Returns:
        A string indicating the winner or if the match was a draw or not scored.
    """
    headers = {
        'Ocp-Apim-Subscription-Key': SPORTS_DATA_IO_NBA_API_KEY
    }
    params = {
        'date': event_date
    }
    try:
        response = requests.get(f"{NBA_API_URL}/scores/json/GamesByDate/{event_date}", headers=headers, params=params)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if fighter1 in game['HomeTeam'] and fighter2 in game['AwayTeam']:
                if game['HomeTeamScore'] > game['AwayTeamScore']:
                    return fighter1
                elif game['HomeTeamScore'] < game['AwayTeamScore']:
                    return fighter2
                else:
                    return "Draw or not scored"
        return "No match found"
    except requests.RequestException as e:
        logging.error(f"API request failed: {e}")
        return "API request failed"

def main():
    # Example fighters and event date
    fighter1 = "Rodolfo Bellato"
    fighter2 = "Paul Craig"
    event_date = "2025-05-17"
    
    result = fetch_ufc_fight_result(fighter1, fighter2, event_date)
    
    if result == fighter1:
        print("recommendation: p2")  # Bellato wins
    elif result == fighter2:
        print("recommendation: p1")  # Craig wins
    elif result == "Draw or not scored":
        print("recommendation: p3")  # Draw or not scored
    else:
        print("recommendation: p4")  # No match found or API request failed

if __name__ == "__main__":
    main()