import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not NHL_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Resolution conditions
RESOLUTION_MAP = {
    "Yes": "p2",  # Leon Draisaitl scores a goal
    "No": "p1",   # Leon Draisaitl does not score a goal
    "50-50": "p3" # Game not completed by the specified date
}

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check if Leon Draisaitl scored in the game
def check_draisaitl_score(game_id):
    url = f"{PROXY_ENDPOINT}/scores/json/BoxScore/{game_id}"
    data = make_request(url, HEADERS)
    if data is None:
        url = f"{PRIMARY_ENDPOINT}/scores/json/BoxScore/{game_id}"
        data = make_request(url, HEADERS)
    if data:
        players = data.get('PlayerGames', [])
        for player in players:
            if player.get('Name') == "Leon Draisaitl":
                goals = player.get('Goals', 0)
                return "Yes" if goals > 0 else "No"
    return "No"

# Main function to resolve the market
def resolve_market():
    game_date = "2025-06-12"
    current_date = datetime.now().strftime("%Y-%m-%d")
    if current_date > "2025-12-31":
        return RESOLUTION_MAP["50-50"]

    url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{game_date}"
    games = make_request(url, HEADERS)
    if games is None:
        url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{game_date}"
        games = make_request(url, HEADERS)
    if games:
        for game in games:
            if game['HomeTeam'] == "EDM" and game['AwayTeam'] == "FLA":
                game_status = game.get('Status')
                if game_status == "Final":
                    result = check_draisaitl_score(game['GameID'])
                    return RESOLUTION_MAP[result]
                else:
                    return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["50-50"]

# Print the recommendation
if __name__ == "__main__":
    recommendation = resolve_market()
    print(f"recommendation: {recommendation}")