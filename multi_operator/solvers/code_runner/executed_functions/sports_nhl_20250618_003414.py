import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Constants
GAME_DATE = "2025-06-17"
PLAYER_NAME = "Sam Reinhart"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Helper function to make API requests
def make_request(url, tag):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during {tag}: {str(e)}")
        return None

# Main function to check if Sam Reinhart scored a goal
def check_player_goal():
    # Format the date for the API request
    formatted_date = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{formatted_date}"

    # Make the API request
    games = make_request(url, "GamesByDate")
    if not games:
        return "recommendation: p4"  # Unable to retrieve data

    # Find the specific game
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == set(TEAM_ABBREVIATIONS.values()):
            # Check if the game status is final
            if game["Status"] != "Final":
                return "recommendation: p4"  # Game not completed

            # Check player stats
            game_id = game["GameID"]
            player_stats_url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByGame/{game_id}"
            player_stats = make_request(player_stats_url, "PlayerGameStatsByGame")
            if not player_stats:
                return "recommendation: p4"  # Unable to retrieve player stats

            # Check if Sam Reinhart scored a goal
            for player_stat in player_stats:
                if player_stat["Name"] == PLAYER_NAME and player_stat["Goals"] > 0:
                    return "recommendation: p2"  # Sam Reinhart scored a goal

            return "recommendation: p1"  # Sam Reinhart did not score a goal

    return "recommendation: p4"  # Game not found

# Run the main function
if __name__ == "__main__":
    result = check_player_goal()
    print(result)