import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants
RESOLUTION_MAP = {
    "NYY": "p2",  # New York Yankees win
    "TBR": "p1",  # Tampa Bay Rays win
    "50-50": "p3",  # Game canceled or postponed without resolution
    "Too early to resolve": "p4"  # Data not available or game not completed
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_game_data():
    """
    Fetches game data for the specified MLB game between New York Yankees and Tampa Bay Rays.
    """
    date = "2025-04-18"
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        
        for game in games:
            if game['HomeTeam'] == 'NYY' and game['AwayTeam'] == 'TBR' or game['HomeTeam'] == 'TBR' and game['AwayTeam'] == 'NYY':
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
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        
        if winner == 'NYY':
            return "recommendation: p2"
        elif winner == 'TBR':
            return "recommendation: p1"
    elif game['Status'] == 'Canceled':
        return "recommendation: p3"
    elif game['Status'] == 'Postponed':
        return "recommendation: p4"  # Market remains open until the game is completed
    
    return "recommendation: p4"  # Default case if none of the above conditions are met

def main():
    """
    Main function to execute the market resolution logic.
    """
    game_data = fetch_game_data()
    result = resolve_market(game_data)
    print(result)

if __name__ == "__main__":
    main()