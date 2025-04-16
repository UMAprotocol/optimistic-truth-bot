import requests
from dotenv import load_dotenv
import os

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
    game_date = "2025-04-15"
    team_tor = "TOR"
    team_buf = "BUF"
    
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={api_key}"
    
    RESOLUTION_MAP = {
        "TOR": "p2",  # Maple Leafs
        "BUF": "p1",  # Sabres
        "50-50": "p3",
        "Too early to resolve": "p4",
    }
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()
        
        for game in games:
            if game['HomeTeam'] == team_tor and game['AwayTeam'] == team_buf or game['HomeTeam'] == team_buf and game['AwayTeam'] == team_tor:
                if game['Status'] == "Final":
                    if game['HomeTeam'] == team_tor and game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP[team_tor]
                    elif game['AwayTeam'] == team_tor and game['AwayTeamScore'] > game['HomeTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP[team_tor]
                    else:
                        return "recommendation: " + RESOLUTION_MAP[team_buf]
                elif game['Status'] == "Postponed":
                    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
                elif game['Status'] == "Canceled":
                    return "recommendation: " + RESOLUTION_MAP["50-50"]
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Example usage
result = fetch_nhl_game_result()
print(result)