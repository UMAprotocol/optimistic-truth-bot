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
GAME_DATE = "2025-06-12"
PLAYER_NAME = "Sam Reinhart"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Resolution map
RESOLUTION_MAP = {
    "Yes": "p2",  # Player scores more than 0.5 goals
    "No": "p1",   # Player does not score more than 0.5 goals
    "50-50": "p3" # Game not completed by the specified date
}

def get_game_data(date, team1, team2):
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if team1 in game['HomeTeam'] and team2 in game['AwayTeam']:
                return game
    except requests.exceptions.RequestException as e:
        print(f"Error accessing primary endpoint: {e}")
        try:
            response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{date}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if team1 in game['HomeTeam'] and team2 in game['AwayTeam']:
                    return game
        except requests.exceptions.RequestException as e:
            print(f"Error accessing proxy endpoint: {e}")
    return None

def check_player_goals(game_id, player_name):
    url = f"{PRIMARY_ENDPOINT}/scores/json/PlayerGameStatsByGame/{game_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        player_stats = response.json()
        for stat in player_stats:
            if player_name in stat['Name']:
                return stat['Goals'] > 0.5
    except requests.exceptions.RequestException:
        return None
    return False

def resolve_market():
    team1 = TEAM_ABBREVIATIONS["Edmonton Oilers"]
    team2 = TEAM_ABBREVIATIONS["Florida Panthers"]
    game = get_game_data(GAME_DATE, team1, team2)
    if not game:
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    if datetime.now() < datetime.strptime("2025-12-31 23:59", "%Y-%m-%d %H:%M"):
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    if game['Status'] != 'Final':
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    player_scored = check_player_goals(game['GameID'], PLAYER_NAME)
    if player_scored is None:
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    if player_scored:
        return "recommendation: " + RESOLUTION_MAP["Yes"]
    else:
        return "recommendation: " + RESOLUTION_MAP["No"]

print(resolve_market())