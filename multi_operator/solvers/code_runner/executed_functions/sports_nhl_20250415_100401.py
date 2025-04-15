import requests
from dotenv import load_dotenv
import os

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
    game_date = "2025-04-14"
    team_abbreviation_map = {
        "Utah": "UTA",  # Assuming Utah has an NHL team with abbreviation UTA
        "Nashville Predators": "NSH"
    }
    RESOLUTION_MAP = {
        "UTA": "p2",
        "NSH": "p1",
        "50-50": "p3",
        "Too early to resolve": "p4"
    }

    try:
        response = requests.get(
            f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}",
            headers={"Ocp-Apim-Subscription-Key": api_key}
        )
        games = response.json()
        for game in games:
            if game['HomeTeam'] == team_abbreviation_map["Utah"] or game['AwayTeam'] == team_abbreviation_map["Utah"]:
                if game['Status'] == "Final":
                    if game['HomeTeam'] == team_abbreviation_map["Utah"] and game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP["UTA"]
                    elif game['AwayTeam'] == team_abbreviation_map["Utah"] and game['AwayTeamScore'] > game['HomeTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP["UTA"]
                    else:
                        return "recommendation: " + RESOLUTION_MAP["NSH"]
                elif game['Status'] == "Postponed":
                    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
                elif game['Status'] == "Canceled":
                    return "recommendation: " + RESOLUTION_MAP["50-50"]
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    except Exception as e:
        print(f"Error fetching game data: {e}")
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Run the function and print the result
print(fetch_nhl_game_result())