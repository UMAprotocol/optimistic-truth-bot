from dotenv import load_dotenv
import os
import requests

def resolve_nba_game():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
    game_date = "2025-04-15"
    team_a = "MEM"  # Memphis Grizzlies
    team_b = "GSW"  # Golden State Warriors

    RESOLUTION_MAP = {
        "MEM": "p2",  # Grizzlies
        "GSW": "p1",  # Warriors
        "50-50": "p3",
        "Too early to resolve": "p4",
    }

    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{game_date}?key={api_key}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] == team_a and game['AwayTeam'] == team_b or game['HomeTeam'] == team_b and game['AwayTeam'] == team_a:
                if game['Status'] == "Scheduled":
                    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
                elif game['Status'] == "Final":
                    if game['HomeTeam'] == team_a and game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP[team_a]
                    elif game['HomeTeam'] == team_b and game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP[team_b]
                    elif game['AwayTeam'] == team_a and game['AwayTeamScore'] > game['HomeTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP[team_a]
                    elif game['AwayTeam'] == team_b and game['AwayTeamScore'] > game['HomeTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP[team_b]
                elif game['Status'] == "Canceled":
                    return "recommendation: " + RESOLUTION_MAP["50-50"]
                elif game['Status'] == "Postponed":
                    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Example usage
print(resolve_nba_game())