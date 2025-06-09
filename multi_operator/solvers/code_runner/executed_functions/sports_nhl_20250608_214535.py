import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
UEFA_NATIONS_LEAGUE_FINAL_DATE = "2025-06-08"
MATCH_TIME = "15:00"  # 3:00 PM ET
PLAYER_NAME = "Gonçalo Ramos"
TEAMS = ("Portugal", "Spain")
RESOLUTION_MAP = {
    "No": "p1",
    "Yes": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Function to check if the player scored
def check_player_score():
    current_date = datetime.utcnow().strftime("%Y-%m-%d")
    current_time = datetime.utcnow().strftime("%H:%M")
    if current_date > UEFA_NATIONS_LEAGUE_FINAL_DATE or (current_date == UEFA_NATIONS_LEAGUE_FINAL_DATE and current_time >= MATCH_TIME):
        try:
            response = requests.get(
                f"https://api.sportsdata.io/v3/soccer/scores/json/PlayerGameStatsByDate/{UEFA_NATIONS_LEAGUE_FINAL_DATE}",
                headers=HEADERS
            )
            if response.status_code == 200:
                games = response.json()
                for game in games:
                    if game['Team'] in TEAMS and game['Opponent'] in TEAMS:
                        for player in game['PlayerGames']:
                            if player['Name'] == PLAYER_NAME:
                                goals = player['Goals']
                                if goals > 0.5:
                                    return "recommendation: " + RESOLUTION_MAP["Yes"]
                                else:
                                    return "recommendation: " + RESOLUTION_MAP["No"]
            return "recommendation: " + RESOLUTION_MAP["50-50"]
        except requests.RequestException as e:
            print(f"Error fetching data: {e}")
            return "recommendation: " + RESOLUTION_MAP["50-50"]
    else:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    result = check_player_score()
    print(result)