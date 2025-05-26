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

# Game details
GAME_DATE = "2025-05-25"
HOME_TEAM = "Red Sox"
AWAY_TEAM = "Orioles"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Red Sox": "p1",  # Home team wins
    "Orioles": "p2",  # Away team wins
    "50-50": "p3",    # Game canceled or postponed without resolution
    "Too early to resolve": "p4"  # Not enough data or game not completed
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

    # Make the API request
    games = make_api_request(url)
    if not games:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    # Find the specific game
    for game in games:
        if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
            if game['Status'] == 'Final':
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return "recommendation: " + RESOLUTION_MAP[HOME_TEAM]
                elif away_score > home_score:
                    return "recommendation: " + RESOLUTION_MAP[AWAY_TEAM]
            elif game['Status'] in ['Canceled', 'Postponed']:
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            else:
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    # If no game matches
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    result = resolve_game()
    print(result)