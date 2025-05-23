import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Check if API key is available
if not MLB_API_KEY:
    raise ValueError("SPORTS_DATA_IO_MLB_API_KEY not found in environment variables.")

# Constants for resolution
RESOLUTION_MAP = {
    "ARI": "p2",  # Arizona Diamondbacks win
    "CHC": "p1",  # Chicago Cubs win
    "50-50": "p3",  # Game canceled or unresolved
    "Too early to resolve": "p4",  # Game not yet played or no data available
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_game_data():
    """
    Fetches game data for the specified MLB game.
    
    Returns:
        A recommendation based on the game outcome.
    """
    date = "2025-04-19"
    team1 = "ARI"
    team2 = "CHC"
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] in [team1, team2] and game['AwayTeam'] in [team1, team2]:
                if game['Status'] == "Final":
                    home_score = game['HomeTeamRuns']
                    away_score = game['AwayTeamRuns']
                    if home_score > away_score:
                        winner = game['HomeTeam']
                    else:
                        winner = game['AwayTeam']
                    return f"recommendation: {RESOLUTION_MAP[winner]}"
                elif game['Status'] in ["Canceled", "Postponed"]:
                    return f"recommendation: {RESOLUTION_MAP['50-50']}"
                else:
                    return f"recommendation: {RESOLUTION_MAP['Too early to resolve']}"
        return f"recommendation: {RESOLUTION_MAP['Too early to resolve']}"

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch game data: {e}")
        return f"recommendation: {RESOLUTION_MAP['Too early to resolve']}"

def main():
    """
    Main function to determine the outcome of the MLB game.
    """
    result = fetch_game_data()
    print(result)

if __name__ == "__main__":
    main()