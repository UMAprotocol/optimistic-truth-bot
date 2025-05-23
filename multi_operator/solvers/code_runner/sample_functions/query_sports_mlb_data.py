"""
MLB market resolver
p1 = Texas Rangers
p2 = Oakland Athletics
p3 = 50-50 (canceled / tie)
p4 = Too early / in-progress
"""
import os, time, logging, re, requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ─────────── configuration ───────────
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()])
logging.getLogger().addFilter(
    lambda r: setattr(r, "msg",
        re.sub(re.escape(API_KEY), "******", r.getMessage())) or True)
log = logging.getLogger(__name__)

# ─────────── generic GET wrapper ───────────
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

# ─────────── helpers ───────────
def team_keys():
    teams = _get("https://api.sportsdata.io/v3/mlb/scores/json/Teams", "Teams")
    m = {}
    for t in teams:
        full = f"{t['City']} {t['Name']}"
        m[full] = t["Key"]               # “Texas Rangers” → “TEX”
        m[t["Name"]] = t["Key"]          # “Rangers” → “TEX”
        if t["Name"].endswith('s'):
            m[t["Name"][:-1]] = t["Key"] # “Athletic” → “ATH”
    # common spoken abbreviations
    m["A's"] = m.get("Athletics", "ATH")
    return m

def final_runs(g):
    a, h = g.get("AwayTeamRuns"), g.get("HomeTeamRuns")
    if a or h:
        return a, h
    a_tot = h_tot = 0
    for inn in g.get("Innings", []):
        a_tot += inn.get("AwayTeamRuns", 0)
        h_tot += inn.get("HomeTeamRuns", 0)
    return a_tot, h_tot

def locate(date_str, k1, k2):
    base = datetime.strptime(date_str, "%Y-%m-%d").date()

    # final slice on local date & +1-day UTC
    for ds in (base, base + timedelta(days=1)):
        url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDateFinal/{ds}"
        for g in _get(url, f"GamesByDateFinal/{ds}"):
            if {g["HomeTeam"], g["AwayTeam"]} == {k1, k2}:
                log.info("Found FINAL boxscore"); return g, "final"

    # season schedule (regular + post)
    season = base.year
    for g in _get(f"https://api.sportsdata.io/v3/mlb/scores/json/Games/{season}",
                  f"Games/{season}"):
        if {g["HomeTeam"], g["AwayTeam"]} == {k1, k2}:
            log.info("Found in schedule feed"); return g, "scheduled"
    log.warning("Matchup not found"); return None, None

def outcome(g, feed, k1, k2):
    if not g or feed == "scheduled":             return "p4"
    if g["Status"] in {"Postponed","Canceled"}:  return "p3"
    if g["Status"] != "Final":                   return "p4"
    a, h = final_runs(g)
    if a == h:                                   return "p3"
    winner = g["HomeTeam"] if h > a else g["AwayTeam"]
    return "p1" if winner == k1 else "p2"

# ─────────── main ───────────
if __name__ == "__main__":
    DATE   = "2025-04-23"
    TEAM1  = "Texas Rangers"       # p1
    TEAM2  = "Athletics"           # p2  (city-less is fine)

    tbl = team_keys()
    k1, k2 = tbl.get(TEAM1, TEAM1), tbl.get(TEAM2, TEAM2)
    log.info(f"Searching with keys: {k1} vs {k2}")

    game, feed = locate(DATE, k1, k2)
    print("recommendation:", outcome(game, feed, k1, k2))