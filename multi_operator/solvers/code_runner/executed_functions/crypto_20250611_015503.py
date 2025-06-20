import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
SPORTS_DATA_IO_NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# API endpoint configuration
WNBA_STATS_ENDPOINT = "https://api.sportsdata.io/v3/wnba/stats/json/PlayerGameStatsByDate"

# Headers for API request
HEADERS = {
    "Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_NBA_API_KEY
}

def fetch_wnba_player_stats(date, player_name):
    """
    Fetch WNBA player stats for a specific game date and player name.
    
    Args:
        date (str): Date of the game in 'YYYY-MM-DD' format.
        player_name (str): Full name of the player.
    
    Returns:
        dict: Player stats including points and rebounds or None if not found.
    """
    response = requests.get(
        WNBA_STATS_ENDPOINT + f"/{date}",
        headers=HEADERS
    )
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if player_name.lower() in (game['Name'].lower()):
                return {
                    "points": game['Points'],
                    "rebounds": game['Rebounds']
                }
    return None

def resolve_market(player_stats):
    """
    Resolve the market based on player stats.
    
    Args:
        player_stats (dict): Dictionary containing points and rebounds of the player.
    
    Returns:
        str: Market resolution recommendation.
    """
    if player_stats is None:
        return "recommendation: p1"  # No data found, resolve as "No"
    
    points = player_stats['points']
    rebounds = player_stats['rebounds']
    
    if points > rebounds:
        return "recommendation: p2"  # Yes, more points than rebounds
    elif points == rebounds:
        return "recommendation: p2"  # Yes, equal points and rebounds
    else:
        return "recommendation: p1"  # No, not more points than rebounds

def main():
    # Specific game date and player name
    game_date = "2025-06-10"
    player_name = "Angel Reese"
    
    # Fetch player stats
    player_stats = fetch_wnba_player_stats(game_date, player_name)
    
    # Resolve the market based on the stats
    resolution = resolve_market(player_stats)
    
    # Output the resolution
    print(resolution)

if __name__ == "__main__":
    main()