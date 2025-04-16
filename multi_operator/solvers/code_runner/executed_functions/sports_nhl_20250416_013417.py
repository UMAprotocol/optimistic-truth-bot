import requests
from dotenv import load_dotenv
import os

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
    game_date = "2025-04-15"
    team_1 = "CBJ"  # Columbus Blue Jackets
    team_2 = "PHI"  # Philadelphia Flyers

    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={api_key}"
    headers = {'Ocp-Apim-Subscription-Key': api_key}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] == team_1 and game['AwayTeam'] == team_2 or game['HomeTeam'] == team_2 and game['AwayTeam'] == team_1:
                if game['Status'] == "Final":
                    home_team_score = game['HomeTeamScore']
                    away_team_score = game['AwayTeamScore']
                    if home_team_score > away_team_score:
                        winning_team = game['HomeTeam']
                    else:
                        winning_team = game['AwayTeam']
                    
                    RESOLUTION_MAP = {
                        "CBJ": "p2",  # Blue Jackets
                        "PHI": "p1",  # Flyers
                        "50-50": "p3",
                        "Too early to resolve": "p4",
                    }
                    
                    return "recommendation: " + RESOLUTION_MAP[winning_team]
                elif game['Status'] == "Postponed":
                    return "recommendation: p4"  # Market remains open
                elif game['Status'] == "Canceled":
                    return "recommendation: p3"  # Resolve 50-50
        return "recommendation: p4"  # No game found or future game
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return "recommendation: p4"  # Unable to resolve due to error

# Example usage
result = fetch_nhl_game_result()
print(result)