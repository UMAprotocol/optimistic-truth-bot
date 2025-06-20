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
PLAYER_NAME = "Jalen Williams"
TEAM_NAME = "Oklahoma City Thunder"
OPPONENT_TEAM = "Indiana Pacers"

# Resolution map
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1",
    "Unknown": "p3"
}

# Function to fetch game data
def fetch_game_data(date):
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Function to determine the outcome
def determine_outcome(games):
    for game in games:
        if game['HomeTeam'] == TEAM_NAME or game['AwayTeam'] == TEAM_NAME:
            if game['Status'] == "Scheduled":
                return RESOLUTION_MAP["Unknown"]
            elif game['Status'] in ["Canceled", "Postponed"]:
                return RESOLUTION_MAP["No"]
            else:
                # Fetch player stats
                game_id = game['GameID']
                player_stats_url = f"https://api.sportsdata.io/v3/nba/stats/json/PlayerGameStatsByGame/{game_id}"
                player_stats_response = requests.get(player_stats_url, headers=HEADERS)
                if player_stats_response.status_code == 200:
                    player_stats = player_stats_response.json()
                    for stat in player_stats:
                        if stat['Name'] == PLAYER_NAME:
                            points = stat['Points']
                            if points > 24.5:
                                return RESOLUTION_MAP["Yes"]
                            else:
                                return RESOLUTION_MAP["No"]
    return RESOLUTION_MAP["No"]

# Main execution
if __name__ == "__main__":
    games = fetch_game_data(GAME_DATE)
    if games:
        recommendation = determine_outcome(games)
    else:
        recommendation = RESOLUTION_MAP["No"]
    print(f"recommendation: {recommendation}")