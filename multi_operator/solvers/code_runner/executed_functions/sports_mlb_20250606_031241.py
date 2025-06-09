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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nba-proxy"

# Game and player details
GAME_DATE = "2025-06-05"
TEAMS = ("Oklahoma City Thunder", "Indiana Pacers")
PLAYER_NAME = "Shai Gilgeous-Alexander"

# Resolution map based on the conditions provided
RESOLUTION_MAP = {
    "yes": "p2",  # Thunder win and SGA scores 34+ points
    "no": "p1"    # Any other outcome
}

def get_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def check_game_and_performance():
    # Construct URL for game data
    game_date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{game_date_formatted}"

    # Fetch game data
    games = get_data(url, HEADERS)
    if not games:
        # Fallback to primary endpoint if proxy fails
        url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{game_date_formatted}"
        games = get_data(url, HEADERS)
        if not games:
            return "p1"  # Resolve to "no" if data cannot be fetched

    # Find the specific game
    for game in games:
        if game['HomeTeam'] in TEAMS and game['AwayTeam'] in TEAMS:
            if game['Status'] != "Final":
                return "p1"  # Game not completed or not started

            # Check game outcome
            thunder_won = (game['Winner'] == "Oklahoma City Thunder")

            # Check player performance
            player_stats_url = f"{PROXY_ENDPOINT}/stats/json/PlayerGameStatsByDate/{game_date_formatted}"
            player_stats = get_data(player_stats_url, HEADERS)
            if not player_stats:
                # Fallback to primary endpoint if proxy fails
                player_stats_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByDate/{game_date_formatted}"
                player_stats = get_data(player_stats_url, HEADERS)
                if not player_stats:
                    return "p1"  # Resolve to "no" if data cannot be fetched

            sga_scored_34_plus = False
            for stat in player_stats:
                if stat['Name'] == PLAYER_NAME and stat['Points'] > 33.5:
                    sga_scored_34_plus = True
                    break

            if thunder_won and sga_scored_34_plus:
                return RESOLUTION_MAP["yes"]
            else:
                return RESOLUTION_MAP["no"]

    return "p1"  # If game not found or other conditions not met

# Main execution
if __name__ == "__main__":
    recommendation = check_game_and_performance()
    print(f"recommendation: {recommendation}")