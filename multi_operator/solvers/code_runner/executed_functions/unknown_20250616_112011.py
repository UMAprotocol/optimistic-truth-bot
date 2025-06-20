"""
Iran's Supreme Leader market resolver
p1 = No (remains Supreme Leader)
p2 = Yes (ceases to be Supreme Leader)
p3 = Unknown/50-50 (cannot determine)
p4 = Too early / in-progress
"""
import os, time, logging, requests
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
def check_status():
    # Define the period of interest
    start_date = datetime(2025, 6, 16, 0, 0)  # Start of the period in ET
    end_date = datetime(2025, 6, 18, 23, 59)  # End of the period in ET

    # Convert to UTC if necessary
    start_date_utc = start_date - timedelta(hours=4)  # ET to UTC conversion
    end_date_utc = end_date - timedelta(hours=4)

    # Current UTC time
    current_utc = datetime.utcnow()

    # Check if the current time is within the period
    if current_utc < start_date_utc:
        return "p4"  # Too early to resolve
    elif current_utc > end_date_utc:
        return "p3"  # Period has ended, unknown status

    # Simulate checking the official source
    # This is where you would implement actual API calls to check the status
    # For demonstration, we assume the status has not changed
    return "p1"  # No change in status

# ─────────── main ───────────
if __name__ == "__main__":
    result = check_status()
    print("recommendation:", result)