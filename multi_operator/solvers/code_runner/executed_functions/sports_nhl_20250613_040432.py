import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API headers
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# NHL game and player specific information
GAME_DATE = "2025-06-12"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}
PLAYER_NAME = "Corey Perry"

# Resolution conditions mapping
RESOLUTION_MAP = {
    "No": "p1",
    "Yes": "p2",
    "50-50": "p3"
}

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error during API request: {e}")
        return None

# Function to check if Corey Perry scored in the game
def check_player_score(game_data):
    for player in game_data.get('PlayerStats', []):
        if player.get('Name') == PLAYER_NAME and player.get('Goals') > 0.5:
            return "Yes"
    return "No"

# Main function to resolve the market
def resolve_market():
    # Construct the API URL
    game_date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date_formatted}"

    # Make the API request
    games = make_request(url, HEADERS)
    if games is None:
        return "Error: Failed to retrieve data."

    # Find the specific game
    for game in games:
        if game['HomeTeam'] == TEAM_ABBREVIATIONS["Florida Panthers"] and game['AwayTeam'] == TEAM_ABBREVIATIONS["Edmonton Oilers"]:
            if game['Status'] != "Final":
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            # Check if Corey Perry scored
            result = check_player_score(game)
            return "recommendation: " + RESOLUTION_MAP[result]

    # If the game is not found or not completed
    current_date = datetime.now()
    game_datetime = datetime.strptime(GAME_DATE + " 20:00", "%Y-%m-%d %H:%M")
    if current_date > game_datetime:
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    else:
        return "recommendation: " + RESOLUTION_MAP["No"]

# Run the main function
if __name__ == "__main__":
    result = resolve_market()
    print(result)