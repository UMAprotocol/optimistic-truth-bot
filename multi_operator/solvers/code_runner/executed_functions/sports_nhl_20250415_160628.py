import requests
from dotenv import load_dotenv
import os

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
    if not api_key:
        return "recommendation: p4"  # API key not found, cannot proceed

    # Define the game details
    team_utah = "UTA"  # Assuming UTA is the abbreviation for Utah in NHL
    team_predators = "NSH"  # Nashville Predators abbreviation
    game_date = "2025-04-14"

    # Define the resolution map
    RESOLUTION_MAP = {
        "UTA": "p2",  # Utah
        "NSH": "p1",  # Nashville Predators
        "50-50": "p3",
        "Too early to resolve": "p4",
    }

    # API endpoint setup
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}"
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()

        # Search for the specific game
        for game in games:
            if game['HomeTeam'] == team_utah and game['AwayTeam'] == team_predators or \
               game['HomeTeam'] == team_predators and game['AwayTeam'] == team_utah:
                if game['Status'] == "Final":
                    if game['HomeTeam'] == team_utah and game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP[team_utah]
                    elif game['HomeTeam'] == team_predators and game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP[team_predators]
                    elif game['AwayTeam'] == team_utah and game['AwayTeamScore'] > game['HomeTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP[team_utah]
                    elif game['AwayTeam'] == team_predators and game['AwayTeamScore'] > game['HomeTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP[team_predators]
                elif game['Status'] == "Postponed":
                    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
                elif game['Status'] == "Canceled":
                    return "recommendation: " + RESOLUTION_MAP["50-50"]
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return "recommendation: p4"  # Error in fetching data

# Call the function and print the result
result = fetch_nhl_game_result()
print(result)