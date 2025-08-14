from __future__ import annotations
import requests, time
from typing import Dict, List

BASE = "https://api.openligadb.de"

def history_to_rows(codes, seasons) -> List[Dict]:
    # Limitato: esempio solo Bundesliga (bl1)
    rows: List[Dict] = []
    for y in seasons:
        r = requests.get(f"{BASE}/getmatchdata/bl1/{y}", timeout=30)
        r.raise_for_status()
        for m in r.json():
            rows.append({
                "date": (m.get("MatchDateTimeUTC") or "")[:10],
                "league": "BL1",
                "home": ((m.get("Team1") or {}).get("TeamName") or ""),
                "away": ((m.get("Team2") or {}).get("TeamName") or ""),
                "home_goals": int((m.get("MatchResults") or [{}])[-1].get("PointsTeam1") or 0),
                "away_goals": int((m.get("MatchResults") or [{}])[-1].get("PointsTeam2") or 0),
            })
        time.sleep(0.4)
    return rows

def upcoming_to_rows(codes) -> List[Dict]:
    r = requests.get(f"{BASE}/getmatchdata/bl1", timeout=20)  # current matchday
    r.raise_for_status()
    out=[]
    for m in r.json():
        out.append({
            "kickoff": (m.get("MatchDateTimeUTC") or ""),
            "league": "BL1",
            "home": ((m.get("Team1") or {}).get("TeamName") or ""),
            "away": ((m.get("Team2") or {}).get("TeamName") or ""),
        })
    return out