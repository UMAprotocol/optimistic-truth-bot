import requests
import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
SPORTS_DATA_IO_NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# NBA API endpoint
NBA_STATS_URL = "https://api.sportsdata.io/v3/nba/stats/json/PlayerGameStatsByDate"

def fetch_game_stats(date, player_name):
    """
    Fetch game statistics for a specific player on a given date from the NBA API.
    
    Args:
        date (str): The date of the game in "YYYY-MM-DD" format.
        player_name (str): Full name of the player to search for.
    
    Returns:
        dict: Dictionary containing points and rebounds or None if data is not found.
    """
    headers = {
        "Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_NBA_API_KEY
    }
    params = {
        "date": date
    }
    try:
        response = requests.get(NBA_STATS_URL, headers=headers, params=params)
        response.raise_for_status()
        games = response.json()
        
        for game in games:
            if player_name.lower() in (game['Name'].lower()):
                return {
                    "points": game['Points'],
                    "rebounds": game['Rebounds']
                }
    except requests.RequestException as e:
        logging.error(f"Failed to fetch data: {str(e)}")
        return None

def resolve_market(points, rebounds):
    """
    Resolve the market based on points and rebounds.
    
    Args:
        points (int): Number of points scored by the player.
        rebounds (int): Number of rebounds by the player.
    
    Returns:
        str: Market resolution recommendation.
    """
    if points >= rebounds:
        return "recommendation: p2"  # Yes, more points than rebounds
    else:
        return "recommendation: p1"  # No, not more points than rebounds

def main():
    # Specific game details
    game_date = "2025-06-10"
    player_name = "Angel Reese"
    
    # Fetch game stats
    stats = fetch_game_stats(game_date, player_name)
    
    if stats:
        # Resolve the market based on the stats
        resolution = resolve_market(stats['points'], stats['rebounds'])
        print(resolution)
    else:
        # If no stats are found or an error occurred, resolve as unknown
        print("recommendation: p4")

if __name__ == "__main__":
    main()