"""
NHL resolver for Avalanche-Stars (23-Apr-2025, 9:30 PM ET)

p1 = Colorado Avalanche
p2 = Dallas Stars
p3 = 50-50  (canceled/tie)
p4 = Too-early / in-progress
"""
import os, time, logging, re, requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ─────────────── configuration ───────────────
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()])
logging.getLogger().addFilter(lambda r: setattr(
    r, "msg", re.sub(re.escape(API_KEY), "******", r.getMessage())) or True)
log = logging.getLogger(__name__)

# ─────────────── HTTP helper ───────────────
def _get(url, tag, retries=3, backoff=1.5):
    for i in range(retries):
        log.debug(f"[{tag}] → {url}")
        r = requests.get(url, headers=HEADERS, timeout=10)
        log.debug(f"[{tag}] ← {r.status_code} {r.reason}")
        if r.ok:
            log.debug(f"[{tag}] payload length: {len(r.json())}")
            return r.json()
        if r.status_code in (401, 403):
            log.error(f"[{tag}] blocked — not in plan"); return None
        if r.status_code == 404:
            log.warning(f"[{tag}] 404 — not found"); return []
        if r.status_code == 429:
            wait = backoff * 2**i
            log.warning(f"[{tag}] 429 — back-off {wait:.1f}s")
            time.sleep(wait); continue
        r.raise_for_status()
    return None

# ─────────────── helpers ───────────────
def team_keys():
    t = _get("https://api.sportsdata.io/v3/nhl/scores/json/Teams", "Teams")
    return {f"{x['City']} {x['Name']}": x['Key'] for x in t}

def fuzzy(name, table):
    name = name.strip().lower()
    return next((k for f,k in table.items() if name in f.lower()), name)

def season_year(d: datetime.date):
    return d.year - 1 if d.month < 7 else d.year    # Playoffs spill into spring

def final_score(game):
    """Return (away, home) as ints, using Periods fallback if top-level zeros."""
    a, h = game.get('AwayTeamScore'), game.get('HomeTeamScore')
    if (a or h):         # not both zero / None
        return a, h
    last_a = last_h = 0
    for p in game.get('Periods', []):
        for sp in p.get('ScoringPlays', []):
            last_a, last_h = sp['AwayTeamScore'], sp['HomeTeamScore']
    return last_a, last_h

def locate(date_str, k1, k2):
    base = datetime.strptime(date_str, "%Y-%m-%d").date()
    # 1️⃣ Finals slice on local date and +1 day (UTC shift)
    for ds in (base, base + timedelta(days=1)):
        url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDateFinal/{ds}"
        for g in _get(url, f"GamesByDateFinal/{ds}"):
            if {g['HomeTeam'], g['AwayTeam']} == {k1, k2}:
                log.info("Found FINAL boxscore"); return g, "final"
    # 2️⃣ Playoff schedule
    post = f"{season_year(base)}POST"
    for g in _get(f"https://api.sportsdata.io/v3/nhl/scores/json/Games/{post}",
                  f"Games/{post}"):
        if g['HomeTeam'] in {k1,k2} and g['AwayTeam'] in {k1,k2}:
            return g, "scheduled"
    # 3️⃣ Regular schedule
    reg = str(season_year(base))
    for g in _get(f"https://api.sportsdata.io/v3/nhl/scores/json/Games/{reg}",
                  f"Games/{reg}"):
        if g['HomeTeam'] in {k1,k2} and g['AwayTeam'] in {k1,k2}:
            return g, "scheduled"
    return None, None

def outcome(g, feed, k1, k2):
    if not g or feed == "scheduled":      return "p4"
    if g['Status'] in {"Postponed","Canceled"}: return "p3"
    if g['Status'] not in {"Final","F/OT","F/SO"}: return "p4"
    a, h = final_score(g)
    if a == h:                            return "p3"
    winner = g['HomeTeam'] if h > a else g['AwayTeam']
    return "p1" if winner == k1 else "p2"

# ─────────────── main ───────────────
if __name__ == "__main__":
    DATE   = "2025-04-23"
    TEAM1  = "Colorado Avalanche"   # p1
    TEAM2  = "Dallas Stars"         # p2

    table = team_keys()
    k1, k2 = fuzzy(TEAM1, table), fuzzy(TEAM2, table)
    log.info(f"Searching with keys: {k1} vs {k2}")

    game, feed = locate(DATE, k1, k2)
    print("recommendation:", outcome(game, feed, k1, k2))