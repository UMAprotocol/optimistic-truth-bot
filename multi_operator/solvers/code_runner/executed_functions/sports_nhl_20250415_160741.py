import requests
from dotenv import load_dotenv
import os

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
    if not api_key:
        return "recommendation: p4"  # API key not found, cannot proceed

    game_date = "2025-04-14"
    team_abbreviation_utah = "UTA"  # Assuming UTA is the abbreviation for Utah in this context
    team_abbreviation_predators = "NSH"  # Nashville Predators abbreviation

    RESOLUTION_MAP = {
        "UTA": "p2",  # Utah wins
        "NSH": "p1",  # Predators win
        "50-50": "p3",
        "Too early to resolve": "p4",
    }

    try:
        response = requests.get(
            f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}",
            headers={"Ocp-Apim-Subscription-Key": api_key}
        )
        games = response.json()

        for game in games:
            if game['Date'][:10] == game_date:
                if game['HomeTeam'] == team_abbreviation_utah or game['AwayTeam'] == team_abbreviation_utah:
                    if game['Status'] == "Final":
                        if game['HomeTeam'] == team_abbreviation_utah and game['HomeTeamScore'] > game['AwayTeamScore']:
                            return "recommendation: " + RESOLUTION_MAP[team_abbreviation_utah]
                        elif game['AwayTeam'] == team_abbreviation_utah and game['AwayTeamScore'] > game['HomeTeamScore']:
                            return "recommendation: " + RESOLUTION_MAP[team_abbreviation_utah]
                        else:
                            return "recommendation: " + RESOLUTION_MAP[team_abbreviation_predators]
                    elif game['Status'] == "Postponed":
                        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
                    elif game['Status'] == "Canceled":
                        return "recommendation: " + RESOLUTION_MAP["50-50"]
    except Exception as e:
        print(f"Error fetching or processing data: {e}")
        return "recommendation: p4"  # Error case

    return "recommendation: p4"  # Default case if no conditions met

# Example usage
result = fetch_nhl_game_result()
print(result)