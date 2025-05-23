import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants
RESOLUTION_MAP = {
    "GSW": "p2",  # Golden State Warriors win
    "HOU": "p1",  # Houston Rockets win
    "50-50": "p3",  # Game canceled or unresolved
    "Too early to resolve": "p4",  # Game not yet played or no data
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nba_game_data(game_date, home_team, away_team):
    """
    Fetch NBA game data from SportsData.io API.
    """
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{game_date}?key={NBA_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                return game
        return None
    except requests.RequestException as e:
        logging.error(f"Error fetching NBA game data: {e}")
        return None

def resolve_market(game_data):
    """
    Resolve the market based on game data.
    """
    if not game_data:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    
    if game_data['Status'] == "Canceled":
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    elif game_data['Status'] == "Final":
        home_score = game_data['HomeTeamScore']
        away_score = game_data['AwayTeamScore']
        if home_score > away_score:
            return "recommendation: " + RESOLUTION_MAP[game_data['HomeTeam']]
        else:
            return "recommendation: " + RESOLUTION_MAP[game_data['AwayTeam']]
    else:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to fetch game data and resolve the market.
    """
    game_date = "2025-04-23"
    home_team = "GSW"
    away_team = "HOU"
    game_data = fetch_nba_game_data(game_date, home_team, away_team)
    result = resolve_market(game_data)
    print(result)

if __name__ == "__main__":
    main()