import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants
RESOLUTION_MAP = {
    "SD": "p2",  # San Diego Padres win
    "HOU": "p1",  # Houston Astros win
    "50-50": "p3",  # Game canceled or postponed without resolution
    "Too early to resolve": "p4",  # Data not available or game not completed
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_game_data():
    """
    Fetches game data for the San Diego Padres vs. Houston Astros game scheduled for April 20, 2025.
    """
    date = "2025-04-20"
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        
        for game in games:
            if game['HomeTeam'] == 'SD' and game['AwayTeam'] == 'HOU' or game['HomeTeam'] == 'HOU' and game['AwayTeam'] == 'SD':
                return game
        return None
    except requests.RequestException as e:
        logging.error(f"Error fetching game data: {e}")
        return None

def resolve_market(game):
    """
    Resolves the market based on the game data.
    """
    if not game:
        return "recommendation: p4"  # No game data found
    
    if game['Status'] == 'Final':
        home_team = game['HomeTeam']
        away_team = game['AwayTeam']
        home_score = game['HomeTeamRuns']
        away_score = game['AwayTeamRuns']
        
        if home_score > away_score:
            winner = home_team
        else:
            winner = away_team
        
        return f"recommendation: {RESOLUTION_MAP.get(winner, 'p3')}"
    elif game['Status'] in ['Canceled', 'Postponed']:
        return "recommendation: p3"
    else:
        return "recommendation: p4"

def main():
    game_data = fetch_game_data()
    result = resolve_market(game_data)
    print(result)

if __name__ == "__main__":
    main()