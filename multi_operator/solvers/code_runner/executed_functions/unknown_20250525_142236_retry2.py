import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
SPORTS_DATA_IO_MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_MLB_API_KEY}

# Function to handle API requests with fallback mechanism
def get_api_response(url, headers, proxy_url=None):
    try:
        response = requests.get(proxy_url if proxy_url else url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            if proxy_url:
                # Fallback to primary endpoint if proxy fails
                return requests.get(url, headers=headers, timeout=10).json()
            response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None

# Function to determine the outcome of the game
def determine_outcome(game_info, team1, team2):
    if not game_info:
        return "p4"  # No game info available, assume in-progress or too early
    if game_info['Status'] in ['Canceled', 'Postponed']:
        return "p3"  # Game canceled or postponed
    if game_info['Status'] == 'Final':
        home_team = game_info['HomeTeam']
        away_team = game_info['AwayTeam']
        home_score = game_info['HomeTeamRuns']
        away_score = game_info['AwayTeamRuns']
        if home_score == away_score:
            return "p3"  # Game ended in a tie
        elif (home_team == team1 and home_score > away_score) or (away_team == team1 and away_score > home_score):
            return "p1"  # Team1 wins
        else:
            return "p2"  # Team2 wins
    return "p4"  # Default to in-progress or too early if status is unclear

# Main function to process the game data
def process_game_data(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{formatted_date}"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    game_data = get_api_response(url, HEADERS, proxy_url)
    
    if game_data:
        for game in game_data:
            if (game['HomeTeam'] == team1 or game['AwayTeam'] == team1) and (game['HomeTeam'] == team2 or game['AwayTeam'] == team2):
                return determine_outcome(game, team1, team2)
    return "p4"  # No relevant game found, assume in-progress or too early

# Example usage
if __name__ == "__main__":
    # Example game details
    game_date = "2025-04-23"
    team1 = "Texas Rangers"
    team2 = "Oakland Athletics"
    recommendation = process_game_data(game_date, team1, team2)
    print(f"recommendation: {recommendation}")