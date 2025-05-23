import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
SPORTS_DATA_IO_NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# API endpoints
NBA_API_URL = "https://api.sportsdata.io/v3/nba"

def fetch_ufc_fight_result(event_date, fighters):
    """
    Fetches the result of a UFC fight from the SportsDataIO NBA API.
    Args:
        event_date: The date of the event in 'YYYY-MM-DD' format.
        fighters: Tuple containing the names of the fighters (fighter1, fighter2).
    Returns:
        A string indicating the winner or 'draw'/'unknown'.
    """
    headers = {
        "Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_NBA_API_KEY
    }
    params = {
        "date": event_date
    }
    try:
        response = requests.get(f"{NBA_API_URL}/scores/json/GamesByDate/{event_date}", headers=headers, params=params)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if fighters[0] in game['HomeTeam'] and fighters[1] in game['AwayTeam']:
                if game['HomeTeamScore'] > game['AwayTeamScore']:
                    return fighters[0]
                elif game['HomeTeamScore'] < game['AwayTeamScore']:
                    return fighters[1]
                else:
                    return "draw"
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        return "unknown"

def main():
    # UFC Fight Night: Machado Garry vs. Prates on April 27, 2025
    event_date = "2025-04-27"
    fighters = ("Evan Elder", "Ahmad Hassanzada")
    result = fetch_ufc_fight_result(event_date, fighters)
    
    if result == fighters[0]:
        print("recommendation: p2")  # Elder wins
    elif result == fighters[1]:
        print("recommendation: p1")  # Hassanzada wins
    elif result == "draw" or result == "unknown":
        print("recommendation: p3")  # Draw or unknown result
    else:
        print("recommendation: p4")  # Unable to determine

if __name__ == "__main__":
    main()