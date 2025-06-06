import os
import requests
import time
import logging
import re
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Configure logging filter to hide API key
logging.getLogger().addFilter(
    lambda r: setattr(r, "msg", re.sub(re.escape(API_KEY), "******", r.getMessage()))
    or True
)

# MLB Team mapping data
MLB_TEAMS = {
    "Los Angeles Angels": {
        "code": "LAA",
        "abbreviation": "LAA",
        "name": "LA Angels",
        "full_name": "Los Angeles Angels",
    },
    "Arizona Diamondbacks": {
        "code": "ARI",
        "abbreviation": "ARI",
        "name": "Arizona",
        "full_name": "Arizona Diamondbacks",
    },
    "Baltimore Orioles": {
        "code": "BAL",
        "abbreviation": "BAL",
        "name": "Baltimore",
        "full_name": "Baltimore Orioles",
    },
    "Boston Red Sox": {
        "code": "BOS",
        "abbreviation": "BOS",
        "name": "Boston",
        "full_name": "Boston Red Sox",
    },
    "Chicago Cubs": {
        "code": "CHC",
        "abbreviation": "CHC",
        "name": "Chi Cubs",
        "full_name": "Chicago Cubs",
    },
    "Cincinnati Reds": {
        "code": "CIN",
        "abbreviation": "CIN",
        "name": "Cincinnati",
        "full_name": "Cincinnati Reds",
    },
    "Cleveland Indians": {
        "code": "CLE",
        "abbreviation": "CLE",
        "name": "Cleveland",
        "full_name": "Cleveland Indians",
    },
    "Colorado Rockies": {
        "code": "COL",
        "abbreviation": "COL",
        "name": "Colorado",
        "full_name": "Colorado Rockies",
    },
    "Detroit Tigers": {
        "code": "DET",
        "abbreviation": "DET",
        "name": "Detroit",
        "full_name": "Detroit Tigers",
    },
    "Houston Astros": {
        "code": "HOU",
        "abbreviation": "HOU",
        "name": "Houston",
        "full_name": "Houston Astros",
    },
    "Kansas City Royals": {
        "code": "KC",
        "abbreviation": "KC",
        "name": "Kansas City",
        "full_name": "Kansas City Royals",
    },
    "Los Angeles Dodgers": {
        "code": "LAD",
        "abbreviation": "LAD",
        "name": "LA Dodgers",
        "full_name": "Los Angeles Dodgers",
    },
    "Washington Nationals": {
        "code": "WSH",
        "abbreviation": "WSH",
        "name": "Washington",
        "full_name": "Washington Nationals",
    },
    "New York Mets": {
        "code": "NYM",
        "abbreviation": "NYM",
        "name": "NY Mets",
        "full_name": "New York Mets",
    },
    "Oakland Athletics": {
        "code": "OAK",
        "abbreviation": "OAK",
        "name": "Oakland",
        "full_name": "Oakland Athletics",
    },
    "Pittsburgh Pirates": {
        "code": "PIT",
        "abbreviation": "PIT",
        "name": "Pittsburgh",
        "full_name": "Pittsburgh Pirates",
    },
    "San Diego Padres": {
        "code": "SD",
        "abbreviation": "SD",
        "name": "San Diego",
        "full_name": "San Diego Padres",
    },
    "Seattle Mariners": {
        "code": "SEA",
        "abbreviation": "SEA",
        "name": "Seattle",
        "full_name": "Seattle Mariners",
    },
    "San Francisco Giants": {
        "code": "SF",
        "abbreviation": "SF",
        "name": "San Francisco",
        "full_name": "San Francisco Giants",
    },
    "St. Louis Cardinals": {
        "code": "STL",
        "abbreviation": "STL",
        "name": "St. Louis",
        "full_name": "St. Louis Cardinals",
    },
    "Tampa Bay Rays": {
        "code": "TB",
        "abbreviation": "TB",
        "name": "Tampa Bay",
        "full_name": "Tampa Bay Rays",
    },
    "Texas Rangers": {
        "code": "TEX",
        "abbreviation": "TEX",
        "name": "Texas",
        "full_name": "Texas Rangers",
    },
    "Toronto Blue Jays": {
        "code": "TOR",
        "abbreviation": "TOR",
        "name": "Toronto",
        "full_name": "Toronto Blue Jays",
    },
    "Minnesota Twins": {
        "code": "MIN",
        "abbreviation": "MIN",
        "name": "Minnesota",
        "full_name": "Minnesota Twins",
    },
    "Philadelphia Phillies": {
        "code": "PHI",
        "abbreviation": "PHI",
        "name": "Philadelphia",
        "full_name": "Philadelphia Phillies",
    },
    "Atlanta Braves": {
        "code": "ATL",
        "abbreviation": "ATL",
        "name": "Atlanta",
        "full_name": "Atlanta Braves",
    },
    "Chicago White Sox": {
        "code": "CHW",
        "abbreviation": "CHW",
        "name": "Chi White Sox",
        "full_name": "Chicago White Sox",
    },
    "Miami Marlins": {
        "code": "MIA",
        "abbreviation": "MIA",
        "name": "Miami",
        "full_name": "Miami Marlins",
    },
    "New York Yankees": {
        "code": "NYY",
        "abbreviation": "NYY",
        "name": "NY Yankees",
        "full_name": "New York Yankees",
    },
    "Milwaukee Brewers": {
        "code": "MIL",
        "abbreviation": "MIL",
        "name": "Milwaukee",
        "full_name": "Milwaukee Brewers",
    },
}

# Create reverse mappings
TEAM_CODE_TO_FULL = {
    team_data["code"]: full_name for full_name, team_data in MLB_TEAMS.items()
}
TEAM_NAME_TO_CODE = {
    full_name: team_data["code"] for full_name, team_data in MLB_TEAMS.items()
}
# Add alternative names
for full_name, team_data in MLB_TEAMS.items():
    TEAM_NAME_TO_CODE[team_data["name"]] = team_data["code"]
    TEAM_NAME_TO_CODE[team_data["abbreviation"]] = team_data["code"]

# Constants
DATE = "2025-06-04"
TEAM1 = "Detroit Tigers"
TEAM2 = "Chicago White Sox"
TEAM1_CODE = TEAM_NAME_TO_CODE.get(TEAM1)
TEAM2_CODE = TEAM_NAME_TO_CODE.get(TEAM2)

if not TEAM1_CODE or not TEAM2_CODE:
    raise ValueError(f"Could not find team codes for {TEAM1} and/or {TEAM2}")

RESOLUTION_MAP = {
    TEAM1_CODE: "p2",  # Detroit Tigers win
    TEAM2_CODE: "p1",  # Chicago White Sox win
    "50-50": "p3",  # Game canceled or tie
    "Too early to resolve": "p4",  # Not enough data or game not completed
}


def _get(url, tag, retries=3, backoff=1.5):
    for i in range(retries):
        log.debug(f"[{tag}] → {url}")
        r = requests.get(url, headers=HEADERS, timeout=10)
        log.debug(f"[{tag}] ← {r.status_code} {r.reason}")
        if r.ok:
            data = r.json()
            log.debug(f"[{tag}] payload length: {len(data)}")
            log.debug(f"[{tag}] full response: {json.dumps(data, indent=2)}")
            return data
        if r.status_code in (401, 403):
            log.error(f"[{tag}] blocked — not in plan")
            log.error(f"[{tag}] error response: {r.text}")
            return None
        if r.status_code == 404:
            log.warning(f"[{tag}] 404 — not found")
            log.warning(f"[{tag}] error response: {r.text}")
            return []
        if r.status_code == 429:
            wait = backoff * 2**i
            log.warning(f"[{tag}] 429 — back-off {wait:.1f}s")
            log.warning(f"[{tag}] error response: {r.text}")
            time.sleep(wait)
            continue
        log.error(f"[{tag}] unexpected error response: {r.text}")
        r.raise_for_status()
    return None


def find_game(date, team1_code, team2_code):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDateFinal/{formatted_date}"
    games = _get(url, "GamesByDateFinal")
    log.debug(f"find_game: got games response: {json.dumps(games, indent=2)}")
    if games is None:
        log.warning("find_game: no games data returned")
        return None, "Too early to resolve"

    team_codes = {team1_code, team2_code}
    for game in games:
        game_teams = {game["HomeTeam"], game["AwayTeam"]}
        log.debug(f"find_game: checking game teams {game_teams} against {team_codes}")
        if game_teams == team_codes:
            log.info(f"find_game: found matching game with status {game['Status']}")
            return game, game["Status"]
    log.warning(f"find_game: no matching game found for {team1_code} vs {team2_code}")
    return None, "Too early to resolve"


def resolve_market(game, status):
    log.debug(
        f"resolve_market: processing game {json.dumps(game, indent=2)} with status {status}"
    )
    if status in ["Final"]:
        home_team = game["HomeTeam"]
        away_team = game["AwayTeam"]
        home_runs = game["HomeTeamRuns"]
        away_runs = game["AwayTeamRuns"]
        log.info(
            f"resolve_market: final score - {home_team}: {home_runs}, {away_team}: {away_runs}"
        )

        winning_team = away_team if away_runs > home_runs else home_team
        log.info(f"resolve_market: winning team is {winning_team}")

        return RESOLUTION_MAP[winning_team]
    elif status in ["Canceled", "Postponed"]:
        log.info(f"resolve_market: game {status}")
        return RESOLUTION_MAP["50-50"]
    log.info("resolve_market: game not in final state")
    return RESOLUTION_MAP["Too early to resolve"]


# Main execution
if __name__ == "__main__":
    log.info(
        f"Starting resolution for {TEAM1}({TEAM1_CODE}) vs {TEAM2}({TEAM2_CODE}) on {DATE}"
    )
    game, status = find_game(DATE, TEAM1_CODE, TEAM2_CODE)
    log.debug(f"Main: got game={json.dumps(game, indent=2)}, status={status}")
    if game and status:
        recommendation = resolve_market(game, status)
    else:
        recommendation = RESOLUTION_MAP["Too early to resolve"]
    log.info(f"Final recommendation: {recommendation}")
    print(f"recommendation: {recommendation}")
