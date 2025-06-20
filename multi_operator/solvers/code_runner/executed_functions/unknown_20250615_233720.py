import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
PGA_TOUR_API_KEY = os.getenv("SPORTS_DATA_IO_GOLF_API_KEY")

# Constants for the event
EVENT_DATE = "2025-06-15"
PLAYER1 = "Scottie Scheffler"
PLAYER2 = "Rory McIlroy"

# PGA Tour API endpoint
PGA_TOUR_ENDPOINT = "https://api.sportsdata.io/v3/golf/scores/json/PlayerTournamentStatsByPlayer"

# Headers for API request
HEADERS = {
    "Ocp-Apim-Subscription-Key": PGA_TOUR_API_KEY
}

def get_player_rank(player_name, tournament_id):
    """
    Fetches the final rank of a player in a specific tournament.
    """
    response = requests.get(
        f"{PGA_TOUR_ENDPOINT}/{tournament_id}/{player_name}",
        headers=HEADERS
    )
    if response.status_code == 200:
        data = response.json()
        return data.get('Rank')
    else:
        return None

def resolve_market(player1_rank, player2_rank):
    """
    Resolves the market based on the ranks of the two players.
    """
    if player1_rank < player2_rank:
        return "p2"  # Scheffler wins
    elif player2_rank < player1_rank:
        return "p1"  # McIlroy wins
    else:
        return "p3"  # Tie

if __name__ == "__main__":
    # Tournament ID for the U.S. Open 2025, this should be predefined or fetched from another endpoint
    tournament_id = "2025_US_OPEN"

    # Get ranks for both players
    scheffler_rank = get_player_rank(PLAYER1, tournament_id)
    mcilroy_rank = get_player_rank(PLAYER2, tournament_id)

    # Resolve the market based on player ranks
    if scheffler_rank is not None and mcilroy_rank is not None:
        recommendation = resolve_market(scheffler_rank, mcilroy_rank)
    else:
        recommendation = "p3"  # If data is missing or there's an error, consider it a tie/unknown

    print(f"recommendation: {recommendation}")