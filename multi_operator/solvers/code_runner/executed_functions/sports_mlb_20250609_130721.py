import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Constants
DATE = "2025-05-28"
TEAM = "Minnesota Timberwolves"
PLAYER = "Anthony Edwards"
GAME_ID = "547785"
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error during request: {e}")
        return None

# Function to check game outcome and player performance
def check_game_and_performance():
    # Construct URL for game data
    game_date = datetime.strptime(DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{game_date}"

    # Make request to proxy endpoint
    game_data = make_request(url, HEADERS)
    if not game_data:
        # Fallback to primary endpoint if proxy fails
        url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{game_date}"
        game_data = make_request(url, HEADERS)
        if not game_data:
            return "p1"  # Resolve to "No" if data cannot be retrieved

    # Find the specific game
    for game in game_data:
        if game['GameID'] == GAME_ID and game['Status'] == "Final":
            if game['AwayTeam'] == TEAM and game['AwayTeamScore'] > game['HomeTeamScore']:
                team_won = True
            elif game['HomeTeam'] == TEAM and game['HomeTeamScore'] > game['AwayTeamScore']:
                team_won = True
            else:
                team_won = False

            # Check player performance
            player_stats_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{GAME_ID}"
            player_stats = make_request(player_stats_url, HEADERS)
            if player_stats:
                for player in player_stats:
                    if player['Name'] == PLAYER and player['Points'] > 27.5:
                        player_met_condition = True
                        break
                else:
                    player_met_condition = False

                if team_won and player_met_condition:
                    return "p2"  # Resolve to "Yes"
            return "p1"  # Resolve to "No" if player data is not satisfactory

    return "p1"  # Resolve to "No" if game is not found or not final

# Main execution
if __name__ == "__main__":
    result = check_game_and_performance()
    print(f"recommendation: {result}")