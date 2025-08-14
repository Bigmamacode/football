from __future__ import annotations
import os, time
from datetime import date
from typing import Dict, List, Iterable
import requests

API_BASE = "https://api.football-data.org/v4"

def _session() -> requests.Session:
    key = os.getenv("FOOTBALL_DATA_API_KEY", "")
    if not key:
        raise RuntimeError("FOOTBALL_DATA_API_KEY non impostata")
    s = requests.Session()
    s.headers.update({"X-Auth-Token": key})
    return s

def competition_matches(code: str, season: int, status: str|None=None) -> List[Dict]:
    """Partite per competizione/season; status: FINISHED, SCHEDULED, TIMED…"""
    with _session() as s:
        params = {"season": str(season)}
        if status: params["status"] = status
        r = s.get(f"{API_BASE}/competitions/{code}/matches", params=params, timeout=30)
        r.raise_for_status()
        return r.json().get("matches", [])

def history_to_rows(codes: Iterable[str], seasons: Iterable[int]) -> List[Dict]:
    rows: List[Dict] = []
    for code in codes:
        for y in seasons:
            for m in competition_matches(code, y, status="FINISHED"):
                ft = (m.get("score") or {}).get("fullTime", {})
                rows.append({
                    "date": (m.get("utcDate") or "").split("T")[0],
                    "league": code,
                    "home": (m.get("homeTeam") or {}).get("name",""),
                    "away": (m.get("awayTeam") or {}).get("name",""),
                    "home_goals": int(ft.get("home") or 0),
                    "away_goals": int(ft.get("away") or 0),
                })
            time.sleep(0.4)  # rate-limit friendly
    return rows

def upcoming_to_rows(codes: Iterable[str]) -> List[Dict]:
    """Prossime partite della season corrente, status=SCHEDULED."""
    rows: List[Dict] = []
    with _session() as s:
        for code in codes:
            # Scopri season corrente
            r = s.get(f"{API_BASE}/competitions/{code}", timeout=20)
            r.raise_for_status()
            comp = r.json()
            start = (comp.get("currentSeason") or {}).get("startDate") or f"{date.today().year}-01-01"
            season_year = int(str(start).split("-")[0])
            for m in competition_matches(code, season_year, status="SCHEDULED"):
                rows.append({
                    "kickoff": m.get("utcDate",""),
                    "league": code,
                    "home": (m.get("homeTeam") or {}).get("name",""),
                    "away": (m.get("awayTeam") or {}).get("name",""),
                })
            time.sleep(0.4)
    return rows