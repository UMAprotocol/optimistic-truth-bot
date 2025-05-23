import os, time, logging, re, requests
from dotenv import load_dotenv
from datetime import datetime

# ───────────────────────── config ─────────────────────────
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NFL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NFL_API_KEY")

HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

RESOLUTION_MAP = {"KC": "p1", "BUF": "p2",
                  "50-50": "p3", "Too early to resolve": "p4"}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
h = logging.StreamHandler()
h.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
h.addFilter(lambda r: setattr(r, "msg",
              re.sub(re.escape(API_KEY), "******", r.getMessage())) or True)
logger.addHandler(h)

# ──────────────────────── helpers ────────────────────────
def _get_json(url, *, retries=3, wait=1.5):
    for i in range(retries):
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (401, 403):
            logger.error(f"Blocked endpoint: {url}")
            return None
        if r.status_code == 429:
            sleep = wait * 2**i
            logger.warning(f"429 rate-limit; retrying in {sleep:.1f}s")
            time.sleep(sleep)
            continue
        if r.status_code == 404:
            logger.warning(f"No data at {url}")
            return []
        r.raise_for_status()
    return None

def get_team_abbreviation_map():
    teams = _get_json("https://api.sportsdata.io/v3/nfl/scores/json/Teams")
    return {f"{t['City']} {t['Name']}": t['Key'] for t in teams} if teams else {}

def fetch_game_data(date_str, team1, team2, team_map):
    t1, t2 = team_map.get(team1, team1), team_map.get(team2, team2)
    url = f"https://api.sportsdata.io/v3/nfl/scores/json/ScoresByDateFinal/{date_str}"
    games = _get_json(url)
    if not games:
        return None

    for g in games:
        if {g['HomeTeam'], g['AwayTeam']} == {t1, t2}:
            g['team1'], g['team2'] = t1, t2
            logger.info(f"Match found: {g['AwayTeam']} @ {g['HomeTeam']}")
            return g
    logger.warning("No matching game on that date")
    return None

def determine_resolution(game):
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]

    status = game['Status']
    hs, as_ = game['HomeScore'], game['AwayScore']
    home, away = game['HomeTeam'], game['AwayTeam']

    if status not in {"Final", "F/OT"}:
        return RESOLUTION_MAP["Too early to resolve"]
    if hs == as_:
        return RESOLUTION_MAP["50-50"]
    winner = home if hs > as_ else away
    return RESOLUTION_MAP.get(winner, RESOLUTION_MAP["50-50"])

# ───────────────────────── main ──────────────────────────
if __name__ == "__main__":
    DATE = "2025-01-15"              # Divisional Rd (example)
    TEAM1, TEAM2 = "Kansas City Chiefs", "Buffalo Bills"

    team_map = get_team_abbreviation_map()
    game = fetch_game_data(DATE, TEAM1, TEAM2, team_map)
    print(f"recommendation: {determine_resolution(game)}")