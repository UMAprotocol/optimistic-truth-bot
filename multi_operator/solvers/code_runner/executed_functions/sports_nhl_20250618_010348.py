import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Game and player details
GAME_DATE = "2025-06-17"
PLAYER_NAME = "Matthew Tkachuk"
TEAMS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Resolution conditions
RESOLUTION_MAP = {
    "Yes": "p2",  # Player scores more than 0.5 goals
    "No": "p1",   # Player does not score more than 0.5 goals
    "50-50": "p3" # Game not completed by the specified date
}

def get_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def check_player_goals(game_id, player_name):
    url = f"{PRIMARY_ENDPOINT}/scores/json/PlayerGameStatsByGame/{game_id}"
    data = get_data(url, HEADERS)
    if data:
        for player in data:
            if player["Name"] == player_name:
                goals = player.get("Goals", 0)
                return "Yes" if goals > 0.5 else "No"
    return "No"

def find_game_id(game_date, team1, team2):
    date_str = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date_str}"
    games = get_data(url, HEADERS)
    if games:
        for game in games:
            if game["HomeTeam"] == team1 and game["AwayTeam"] == team2:
                return game["GameID"]
            elif game["HomeTeam"] == team2 and game["AwayTeam"] == team1:
                return game["GameID"]
    return None

def main():
    game_id = find_game_id(GAME_DATE, TEAMS["Edmonton Oilers"], TEAMS["Florida Panthers"])
    if game_id:
        result = check_player_goals(game_id, PLAYER_NAME)
        print("recommendation:", RESOLUTION_MAP[result])
    else:
        print("recommendation:", RESOLUTION_MAP["50-50"])

if __name__ == "__main__":
    main()