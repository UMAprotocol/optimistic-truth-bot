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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}
GAME_DATE = "2025-06-17"
PLAYER_NAME = "Aleksander Barkov"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Resolution map
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1",
    "50-50": "p3"
}

def get_game_data(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{formatted_date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            raise Exception("Failed to fetch data from primary endpoint, trying proxy.")
    except:
        response = requests.get(f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{formatted_date}", headers=HEADERS, timeout=10)
        if not response.ok:
            raise Exception("Failed to fetch data from both primary and proxy endpoints.")

    games = response.json()
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            return game
    return None

def check_player_goals(game_id, player_name):
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            raise Exception("Failed to fetch player stats from primary endpoint, trying proxy.")
    except:
        response = requests.get(f"{PROXY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}", headers=HEADERS, timeout=10)
        if not response.ok:
            raise Exception("Failed to fetch player stats from both primary and proxy endpoints.")

    players_stats = response.json()
    for stat in players_stats:
        if stat["Name"] == player_name:
            return stat["Goals"] > 0.5
    return False

def resolve_market():
    game = get_game_data(GAME_DATE, TEAM_ABBREVIATIONS["Edmonton Oilers"], TEAM_ABBREVIATIONS["Florida Panthers"])
    if not game:
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    if datetime.now() < datetime.strptime(GAME_DATE + " 23:59", "%Y-%m-%d %H:%M"):
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    if game["Status"] != "Final":
        return "recommendation: " + RESOLUTION_MAP["50-50"]

    player_scored = check_player_goals(game["GameID"], PLAYER_NAME)
    if player_scored:
        return "recommendation: " + RESOLUTION_MAP["Yes"]
    else:
        return "recommendation: " + RESOLUTION_MAP["No"]

if __name__ == "__main__":
    print(resolve_market())