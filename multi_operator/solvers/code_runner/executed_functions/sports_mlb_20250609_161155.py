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
        if endpoint == PROXY_ENDPOINT:
            print("Proxy failed, trying primary endpoint")
            return make_request(PRIMARY_ENDPOINT, path)
        else:
            print(f"Error: {e}")
            return None

# Function to find and analyze the game data
def analyze_game():
    date_str = "2025-05-29"
    player_name = "Tyrese Haliburton"
    team = "Indiana Pacers"
    opponent = "New York Knicks"

    # Convert date to required format and construct API path
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%Y-%b-%d").upper()
    path = f"/scores/json/GamesByDate/{formatted_date}"

    # Make the API request
    games = make_request(PROXY_ENDPOINT, path)
    if games is None:
        return "recommendation: p1"  # Resolve to "No" if data retrieval fails

    # Find the specific game
    for game in games:
        if game['HomeTeam'] == team or game['AwayTeam'] == team:
            if game['HomeTeam'] == opponent or game['AwayTeam'] == opponent:
                # Check if game status indicates cancellation or postponement
                if game['Status'] != 'Final':
                    return "recommendation: p1"  # Game not completed as scheduled

                # Retrieve player stats
                game_id = game['GameID']
                player_stats_path = f"/stats/json/PlayerGameStatsByGame/{game_id}"
                player_stats = make_request(PROXY_ENDPOINT, player_stats_path)
                if player_stats is None:
                    return "recommendation: p1"  # Resolve to "No" if data retrieval fails

                # Check player's points
                for stat in player_stats:
                    if stat['Name'] == player_name:
                        points = stat['Points']
                        if points > 22.5:
                            return "recommendation: p2"  # Yes, scored more than 22.5 points
                        else:
                            return "recommendation: p1"  # No, did not score more than 22.5 points

    return "recommendation: p1"  # Default to "No" if no matching game or stats found

# Main execution
if __name__ == "__main__":
    result = analyze_game()
    print(result)