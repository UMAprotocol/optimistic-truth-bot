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
NBA_API_URL = "https://api.sportsdata.io/v3/nba"

def fetch_ufc_fight_result(fight_date, fighters):
    """
    Fetches the result of a UFC fight from the SportsDataIO NBA API.
    Args:
        fight_date (str): The date of the fight in YYYY-MM-DD format.
        fighters (tuple): A tuple containing the names of the fighters.

    Returns:
        str: The result of the fight or 'unknown' if the result cannot be determined.
    """
    headers = {
        'Ocp-Apim-Subscription-Key': SPORTS_DATA_IO_NBA_API_KEY
    }
    params = {
        'date': fight_date
    }
    try:
        response = requests.get(f"{NBA_API_URL}/scores/json/GamesByDate/{fight_date}", headers=headers, params=params)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if fighters[0] in game['HomeTeam'] and fighters[1] in game['AwayTeam']:
                if game['HomeTeamScore'] > game['AwayTeamScore']:
                    return fighters[0]
                elif game['HomeTeamScore'] < game['AwayTeamScore']:
                    return fighters[1]
                else:
                    return 'draw'
    except requests.RequestException as e:
        logging.error(f"API request failed: {e}")
        return 'unknown'
    return 'unknown'

def main():
    fight_date = "2025-05-17"
    fighters = ("Rodolfo Bellato", "Paul Craig")
    result = fetch_ufc_fight_result(fight_date, fighters)
    if result == fighters[0]:
        print("recommendation: p2")
    elif result == fighters[1]:
        print("recommendation: p1")
    elif result == 'draw':
        print("recommendation: p3")
    else:
        print("recommendation: p3")

if __name__ == "__main__":
    main()