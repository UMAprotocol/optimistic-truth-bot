import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not NHL_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
DATE = "2025-06-04"
TEAM_ABBR_EDMONTON = "EDM"
TEAM_ABBR_FLORIDA = "FLA"
PLAYER_NAME = "Connor McDavid"

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check if Connor McDavid scored
def check_mcdavid_score(game_id):
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    game_stats = make_request(url, HEADERS)
    if game_stats:
        for stat in game_stats:
            if stat['Name'] == PLAYER_NAME and stat['Goals'] >= 1:
                return True
    return False

# Function to find the game and check the score
def resolve_market():
    date_formatted = datetime.strptime(DATE, "%Y-%m-%d").strftime("%Y-%b-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date_formatted}"
    games = make_request(url, HEADERS)
    if games:
        for game in games:
            if game['HomeTeam'] == TEAM_ABBR_FLORIDA and game['AwayTeam'] == TEAM_ABBR_EDMONTON:
                if game['Status'] == "Final":
                    if check_mcdavid_score(game['GameID']):
                        return "recommendation: p2"  # McDavid scored
                    else:
                        return "recommendation: p1"  # McDavid did not score
                else:
                    return "recommendation: p1"  # Game not completed or McDavid did not play
    return "recommendation: p1"  # No game found or other issues

# Main execution
if __name__ == "__main__":
    result = resolve_market()
    print(result)