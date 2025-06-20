import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
SPORTS_DATA_IO_NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants for API endpoints
NBA_API_URL = "https://api.sportsdata.io/v3/nba"

# Define the resolution map according to the ancillary data
RESOLUTION_MAP = {
    "Craig": "p1",
    "Bellato": "p2",
    "Unknown": "p3"
}

def fetch_ufc_fight_result(fighter1, fighter2, event_date):
    """
    Fetches the result of a UFC fight from the Sports Data IO NBA API.
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
            if fighter1 in game['HomeTeam'] and fighter2 in game['AwayTeam']:
                if game['HomeTeamScore'] > game['AwayTeamScore']:
                    return fighter1
                elif game['HomeTeamScore'] < game['AwayTeamScore']:
                    return fighter2
                else:
                    return "Unknown"
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        return "Unknown"

def main():
    # Specific fight details
    fighter1 = "Rodolfo Bellato"
    fighter2 = "Paul Craig"
    event_date = "2025-05-17"

    # Fetch the fight result
    result = fetch_ufc_fight_result(fighter1, fighter2, event_date)

    # Determine the resolution based on the fight result
    resolution = RESOLUTION_MAP.get(result, "p3")  # Default to "Unknown" if result is not found

    # Output the recommendation
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()