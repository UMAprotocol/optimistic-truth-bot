import os
import requests
from dotenv import load_dotenv
import logging

# ─────────── configuration ───────────
load_dotenv()
PGA_TOUR_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")  # Using NHL key as a placeholder for PGA Tour
if not PGA_TOUR_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": PGA_TOUR_API_KEY}

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()])
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

# ─────────── main ───────────
def main():
    TOURNAMENT_DATE = "2025-06-01"
    PLAYER1 = "Scottie Scheffler"
    PLAYER2 = "Xander Schauffele"

    # Fetch tournament results
    url = f"https://api.sportsdata.io/v3/golf/scores/json/Leaderboard/{TOURNAMENT_DATE}"
    results = _get(url, "TournamentResults")
    if not results:
        print("recommendation: p4")
        return

    # Determine the final positions
    scheffler_position = next((player['Position'] for player in results if player['Player'] == PLAYER1), None)
    schauffele_position = next((player['Position'] for player in results if player['Player'] == PLAYER2), None)

    # Compare positions
    if scheffler_position is None or schauffele_position is None:
        print("recommendation: p4")
        return

    if scheffler_position < schauffele_position:
        print("recommendation: p2")
    elif schauffele_position < scheffler_position:
        print("recommendation: p1")
    else:
        # Tiebreaker based on world rankings
        scheffler_rank = next((player['WorldRanking'] for player in results if player['Player'] == PLAYER1), None)
        schauffele_rank = next((player['WorldRanking'] for player in results if player['Player'] == PLAYER2), None)
        if scheffler_rank < schauffele_rank:
            print("recommendation: p2")
        else:
            print("recommendation: p1")

if __name__ == "__main__":
    main()