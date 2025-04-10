import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants for the game
GAME_DATE = "2025-04-09"
GAME_TIME = "19:30:00"
TEAM_HOME = "New York Rangers"
TEAM_AWAY = "Philadelphia Flyers"

# API Key for Sports Data IO
SPORTS_DATA_IO_API_KEY = os.getenv('SPORTS_DATA_IO_MLB_API_KEY')

# API URL
API_URL = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{}?key={}".format(GAME_DATE, SPORTS_DATA_IO_API_KEY)

def fetch_game_data():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        games = response.json()
        
        # Find the game between the specified teams
        for game in games:
            if (game['HomeTeam'] == TEAM_HOME and game['AwayTeam'] == TEAM_AWAY) or \
               (game['HomeTeam'] == TEAM_AWAY and game['AwayTeam'] == TEAM_HOME):
                return game
        return None
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return None

def resolve_market(game):
    if not game:
        print("Game data not found.")
        return "recommendation: p3"
    
    if game['Status'] == "Canceled":
        return "recommendation: p3"
    elif game['Status'] == "Postponed":
        # Since the market remains open for postponed games, we cannot resolve it now
        return "recommendation: p4"
    elif game['Status'] == "Final":
        if game['HomeTeam'] == TEAM_HOME:
            home_score = game['HomeTeamScore']
            away_score = game['AwayTeamScore']
        else:
            home_score = game['AwayTeamScore']
            away_score = game['HomeTeamScore']
        
        if home_score > away_score:
            return "recommendation: p1" if TEAM_HOME == "New York Rangers" else "recommendation: p2"
        else:
            return "recommendation: p2" if TEAM_HOME == "New York Rangers" else "recommendation: p1"
    else:
        return "recommendation: p4"

def main():
    game_data = fetch_game_data()
    result = resolve_market(game_data)
    print(result)

if __name__ == "__main__":
    main()