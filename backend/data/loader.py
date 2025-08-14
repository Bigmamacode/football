from __future__ import annotations
from typing import List, Dict
from datetime import datetime, timedelta
import os, time

# ---- MOCK CERTI ----
def get_mock_history() -> List[Dict]:
    return [
        {"date":"2025-08-01","home":"Milan","away":"Inter","home_goals":1,"away_goals":2},
        {"date":"2025-08-02","home":"Juventus","away":"Roma","home_goals":2,"away_goals":1},
        {"date":"2025-08-03","home":"Napoli","away":"Lazio","home_goals":3,"away_goals":1},
        {"date":"2025-08-04","home":"Inter","away":"Juventus","home_goals":1,"away_goals":1},
        {"date":"2025-08-05","home":"Roma","away":"Napoli","home_goals":0,"away_goals":2},
        {"date":"2025-08-06","home":"Lazio","away":"Milan","home_goals":2,"away_goals":2},
    ]

def get_mock_matches() -> List[Dict]:
    today = datetime.utcnow().date()
    iso = lambda d: datetime.combine(d, datetime.min.time()).isoformat()
    return [
        {"kickoff": iso(today + timedelta(days=1)), "home":"Milan",    "away":"Roma",   "league":"Serie A"},
        {"kickoff": iso(today + timedelta(days=1)), "home":"Juventus", "away":"Lazio",  "league":"Serie A"},
        {"kickoff": iso(today + timedelta(days=2)), "home":"Inter",    "away":"Napoli", "league":"Serie A"},
    ]

# ---- API (opzionale) + FALLBACK ----
FORCE_MOCK = os.getenv("FORCE_MOCK","").lower() in ("1","true","yes","on")
LEAGUE_CODES = [c.strip() for c in os.getenv("LEAGUE_CODES","SA,PL,PD,BL1,FL1").split(",") if c.strip()]
SEASONS = [int(y) for y in os.getenv("SEASONS","2022,2023,2024").split(",") if y.strip()]
API_KEY = os.getenv("FOOTBALL_DATA_API_KEY","")

def get_history() -> List[Dict]:
    if FORCE_MOCK:
        return get_mock_history()
    if API_KEY:
        try:
            from .providers.football_data import history_to_rows
            rows = history_to_rows(LEAGUE_CODES, SEASONS)
            if rows: return rows
            print("[loader] API history returned 0 rows, using mock"); time.sleep(0.1)
        except Exception as e:
            print("[loader] API history failed, using mock:", e)
    return get_mock_history()

def get_matches() -> List[Dict]:
    if FORCE_MOCK:
        return get_mock_matches()
    if API_KEY:
        try:
            from .providers.football_data import upcoming_to_rows
            rows = upcoming_to_rows(LEAGUE_CODES)
            rows = [r for r in rows if (r.get("home") and r.get("away"))]
            if rows: return rows
            print("[loader] API upcoming returned 0 rows, using mock"); time.sleep(0.1)
        except Exception as e:
            print("[loader] API upcoming failed, using mock:", e)
    return get_mock_matches()