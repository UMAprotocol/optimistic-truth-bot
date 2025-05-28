import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
NBA_URL = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/"
NHL_URL = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/"
HEADERS_NBA = {"Ocp-Apim-Subscription-Key": NBA_API_KEY}
HEADERS_NHL = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}
DATE = "2025-05-26"

# Function to check game results
def check_game_results(url, headers, team):
    response = requests.get(url + DATE, headers=headers)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if (game['HomeTeam'] == team or game['AwayTeam'] == team) and game['Status'] == "Final":
                if game['Winner'] == team:
                    return True
                else:
                    return False
    return None

# Main function to resolve the market
def resolve_market():
    thunder_win = check_game_results(NBA_URL, HEADERS_NBA, "OKC")
    panthers_win = check_game_results(NHL_URL, HEADERS_NHL, "FLA")

    if thunder_win is None or panthers_win is None:
        return "recommendation: p4"  # Unable to resolve now
    if thunder_win and panthers_win:
        return "recommendation: p2"  # Yes, both win
    else:
        return "recommendation: p1"  # No, one or both did not win

# Execute the main function
if __name__ == "__main__":
    result = resolve_market()
    print(result)