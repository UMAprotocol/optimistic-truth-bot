import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration for headers and API endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Function to make API requests
def make_request(endpoint, path, use_proxy=False):
    url = f"{PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT}{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_request(endpoint, path, use_proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to check the game result and player performance
def check_game_and_performance(date, team, player):
    # Format the date for the API request
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(PRIMARY_ENDPOINT, f"/scores/json/GamesByDate/{formatted_date}")

    if games_today:
        for game in games_today:
            if team in [game['HomeTeam'], game['AwayTeam']]:
                game_id = game['GameID']
                stats = make_request(PRIMARY_ENDPOINT, f"/stats/json/PlayerGameStatsByGame/{game_id}")
                if stats:
                    for stat in stats:
                        if stat['Name'] == player:
                            points = stat['Points']
                            team_won = (game['Status'] == 'Final' and 
                                        ((game['HomeTeam'] == team and game['HomeTeamScore'] > game['AwayTeamScore']) or
                                         (game['AwayTeam'] == team and game['AwayTeamScore'] > game['HomeTeamScore'])))
                            if team_won and points > 17.5:
                                return "p2"  # Yes
                            else:
                                return "p1"  # No
    return "p1"  # No if game not found or conditions not met

# Main function to run the check
def main():
    date = "2025-06-05"
    team = "Indiana Pacers"
    player = "Tyrese Haliburton"
    result = check_game_and_performance(date, team, player)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()