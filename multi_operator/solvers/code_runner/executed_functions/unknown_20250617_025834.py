import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during request to {endpoint}/{path}: {str(e)}")
        return None

# Function to check the match and calculate the total goals
def check_match_and_goals(date, team1, team2):
    # Format the date for the API request
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(PROXY_ENDPOINT, f"GamesByDate/{formatted_date}")
    if not games_today:
        games_today = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{formatted_date}")
    
    if games_today:
        for game in games_today:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or \
               (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                total_goals = game['HomeTeamScore'] + game['AwayTeamScore']
                return total_goals
    return None

# Main function to determine the outcome
def main():
    match_date = "2025-06-16"
    team1 = "Flamengo"
    team2 = "Esperance Sportive de Tunis"
    total_goals = check_match_and_goals(match_date, team1, team2)
    
    if total_goals is None:
        print("recommendation: p3")  # Unknown or match not found
    elif total_goals > 2.5:
        print("recommendation: p2")  # Yes, more than 2.5 goals
    else:
        print("recommendation: p1")  # No, not more than 2.5 goals

if __name__ == "__main__":
    main()