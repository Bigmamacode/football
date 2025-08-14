from __future__ import annotations
from typing import List, Dict
from datetime import datetime, timedelta
import os, time

# ---- MOCK ----
def get_mock_history() -> List[Dict]:
    return [
        {"date":"2025-08-01","home":"Milan","away":"Inter","home_goals":1,"away_goals":2},
        {"date":"2025-08-02","home":"Juventus","away":"Roma","home_goals":2,"away_goals":1},
        {"date":"2025-08-03","home":"Napoli","away":"Lazio","home_goals":3,"away_goals":1},
        {"date":"2025-08-04","home":"Inter","away":"Juventus","home_goals":1,"away_goals":1},
    ]

def get_mock_matches() -> List[Dict]:
    today = datetime.utcnow().date()
    iso = lambda d: datetime.combine(d, datetime.min.time()).isoformat()
    return [
        {"kickoff": iso(today + timedelta(days=1)), "home":"Milan", "away":"Roma", "league":"Serie A"},
        {"kickoff": iso(today + timedelta(days=1)), "home":"Juventus", "away":"Lazio","league":"Serie A"},
        {"kickoff": iso(today + timedelta(days=2)), "home":"Inter", "away":"Napoli","league":"Serie A"},
    ]

# ---- Config ----
FORCE_MOCK   = os.getenv("FORCE_MOCK","").lower() in ("1","true","yes","on")
DATA_PROVIDER= (os.getenv("DATA_PROVIDER","FDORG") or "FDORG").upper()   # FDORG | APIFOOTBALL | OPENLIGADB
LEAGUE_CODES = [c.strip() for c in os.getenv("LEAGUE_CODES","SA,PL,PD,BL1,FL1").split(",") if c.strip()]
SEASONS      = [int(y) for y in os.getenv("SEASONS","2022,2023,2024").split(",") if y.strip()]
API_KEY_FD   = os.getenv("FOOTBALL_DATA_API_KEY","")
API_KEY_AF   = os.getenv("API_FOOTBALL_KEY","")

def _pick():
    if DATA_PROVIDER == "APIFOOTBALL":   # richiede API_FOOTBALL_KEY
        from .providers import api_football as P
        return P
    if DATA_PROVIDER == "OPENLIGADB":    # nessuna chiave, soprattutto BL1
        from .providers import openligadb as P
        return P
    # default: football-data.org (richiede FOOTBALL_DATA_API_KEY)
    from .providers import football_data as P
    return P

def get_history() -> List[Dict]:
    if FORCE_MOCK: return get_mock_history()
    try:
        P = _pick()
        rows = P.history_to_rows(LEAGUE_CODES, SEASONS)
        if rows: return rows
        print(f"[loader] history empty ({DATA_PROVIDER}), using mock")
    except Exception as e:
        print(f"[loader] history failed ({DATA_PROVIDER}):", e)
    return get_mock_history()

def get_matches() -> List[Dict]:
    if FORCE_MOCK: return get_mock_matches()
    try:
        P = _pick()
        rows = P.upcoming_to_rows(LEAGUE_CODES)
        rows = [r for r in (rows or []) if (r.get("home") and r.get("away"))]
        if rows: return rows
        print(f"[loader] upcoming empty ({DATA_PROVIDER}), using mock")
    except Exception as e:
        print(f"[loader] upcoming failed ({DATA_PROVIDER}):", e)
    return get_mock_matches()