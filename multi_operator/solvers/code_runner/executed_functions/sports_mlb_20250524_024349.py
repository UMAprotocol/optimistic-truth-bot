import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Function to make API requests
def make_request(endpoint, path):
    url = f"{endpoint}{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check game and player performance
def check_game_and_performance(date, team, player):
    # Format date for API endpoint
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_endpoint = f"/scores/json/GamesByDate/{formatted_date}"

    # Try proxy first
    games = make_request(PROXY_ENDPOINT, games_endpoint)
    if games is None:
        games = make_request(PRIMARY_ENDPOINT, games_endpoint)
        if games is None:
            return "p4"  # Unable to retrieve data

    # Find the specific game
    for game in games:
        if team in (game['HomeTeam'], game['AwayTeam']):
            game_id = game['GameID']
            break
    else:
        return "p4"  # Game not found

    # Check player stats
    player_stats_endpoint = f"/stats/json/PlayerGameStatsByDate/{formatted_date}"
    player_stats = make_request(PROXY_ENDPOINT, player_stats_endpoint)
    if player_stats is None:
        player_stats = make_request(PRIMARY_ENDPOINT, player_stats_endpoint)
        if player_stats is None:
            return "p4"  # Unable to retrieve data

    # Analyze game outcome and player performance
    pacers_win = any(gs for gs in games if gs['GameID'] == game_id and team in (gs['HomeTeam'], gs['AwayTeam']) and gs['Status'] == "Final" and ((gs['HomeTeam'] == team and gs['HomeTeamScore'] > gs['AwayTeamScore']) or (gs['AwayTeam'] == team and gs['AwayTeamScore'] > gs['HomeTeamScore'])))
    haliburton_21_plus = any(ps for ps in player_stats if ps['GameID'] == game_id and ps['Name'] == player and ps['Points'] > 20.5)

    if pacers_win and haliburton_21_plus:
        return "p2"  # Yes
    else:
        return "p1"  # No

# Main function to run the check
if __name__ == "__main__":
    game_date = "2025-05-23"
    team_name = "Indiana Pacers"
    player_name = "Tyrese Haliburton"
    recommendation = check_game_and_performance(game_date, team_name, player_name)
    print(f"recommendation: {recommendation}")