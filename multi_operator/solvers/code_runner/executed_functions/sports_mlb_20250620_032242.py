import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
GAME_DATE = "2025-06-19"
PLAYER_NAME = "Tyrese Haliburton"
TEAM_ABBREVIATION = "IND"  # Indiana Pacers
OPPONENT_ABBREVIATION = "OKC"  # Oklahoma City Thunder
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1",
    "Unknown": "p3"
}

# Helper function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Main function to resolve the market
def resolve_market():
    # Construct the URL for the game data
    url = f"https://api.sportsdata.io/v3/nba/stats/json/PlayerGameStatsByDate/{GAME_DATE}"
    games_data = make_request(url, HEADERS)
    
    if not games_data:
        return "recommendation: p3"  # Unknown if no data is available

    # Find the game and player stats
    for game in games_data:
        if game['Team'] == TEAM_ABBREVIATION and game['Opponent'] == OPPONENT_ABBREVIATION:
            for player in game['PlayerGames']:
                if player['Name'] == PLAYER_NAME:
                    points = player['Points']
                    if points is not None:
                        if points > 15.5:
                            return f"recommendation: {RESOLUTION_MAP['Yes']}"
                        else:
                            return f"recommendation: {RESOLUTION_MAP['No']}"
    
    # If no matching game or player stats are found
    return f"recommendation: {RESOLUTION_MAP['No']}"

# Execute the function and print the result
if __name__ == "__main__":
    result = resolve_market()
    print(result)