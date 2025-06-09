import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
UEFA_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")  # Using NHL key as placeholder, replace with actual UEFA key if available

# Constants
MATCH_DATE = "2025-06-08"
MATCH_TIME = "15:00"  # 3:00 PM ET
PLAYER_NAME = "Gonçalo Ramos"
TEAM_PORTUGAL = "Portugal"
TEAM_SPAIN = "Spain"
UEFA_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"
HEADERS = {"Ocp-Apim-Subscription-Key": UEFA_API_KEY}

# Function to fetch match data
def fetch_match_data(date):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = UEFA_ENDPOINT.format(date=formatted_date)
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Function to check if player scored
def check_player_score(matches, player_name, team1, team2):
    for match in matches:
        if (match['HomeTeam'] == team1 and match['AwayTeam'] == team2) or (match['HomeTeam'] == team2 and match['AwayTeam'] == team1):
            # Assuming structure where player goals are listed, this part needs to be adjusted based on actual API response structure
            for player in match['Players']:
                if player['Name'] == player_name and player['Goals'] > 0:
                    return True
    return False

# Main execution
def main():
    matches = fetch_match_data(MATCH_DATE)
    if not matches:
        print("recommendation: p4")  # Unable to fetch data
        return

    if check_player_score(matches, PLAYER_NAME, TEAM_PORTUGAL, TEAM_SPAIN):
        print("recommendation: p2")  # Player scored
    else:
        print("recommendation: p1")  # Player did not score

if __name__ == "__main__":
    main()