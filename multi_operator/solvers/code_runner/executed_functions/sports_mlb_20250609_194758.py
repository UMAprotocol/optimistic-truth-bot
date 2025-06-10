import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Constants for the game
GAME_DATE = "2025-05-31"
TEAM_HOME = "Orioles"
TEAM_AWAY = "White Sox"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    TEAM_HOME: "p1",  # Orioles win
    TEAM_AWAY: "p2",  # White Sox win
    "50-50": "p3",    # Game canceled or unresolved
    "Too early to resolve": "p4"  # Not enough data or future game
}

# Function to make API requests
def make_api_request(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
        return None

# Function to find and resolve the game outcome
def resolve_game():
    # Format the date for the API endpoint
    formatted_date = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{formatted_date}"

    games = make_api_request(url)
    if not games:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    # Search for the specific game
    for game in games:
        if game['HomeTeam'] == TEAM_HOME and game['AwayTeam'] == TEAM_AWAY:
            if game['Status'] == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return "recommendation: " + RESOLUTION_MAP[TEAM_HOME]
                elif away_score > home_score:
                    return "recommendation: " + RESOLUTION_MAP[TEAM_AWAY]
            elif game['Status'] == "Canceled":
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            elif game['Status'] == "Postponed":
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    result = resolve_game()
    print(result)