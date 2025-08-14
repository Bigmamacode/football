from __future__ import annotations
import os, time
from typing import Dict, List, Iterable
import requests

API_BASE = "https://v3.football.api-sports.io"

# mapping leghe comuni -> id API-Football
LEAGUE_MAP = { "SA":135, "PL":39, "PD":140, "BL1":78, "FL1":61 }

def _s() -> requests.Session:
    key = os.getenv("API_FOOTBALL_KEY","")
    if not key: raise RuntimeError("API_FOOTBALL_KEY missing")
    s = requests.Session()
    s.headers.update({"x-apisports-key": key})
    return s

def _ids(codes: Iterable[str]) -> List[int]:
    out=[]
    for c in codes:
        if c in LEAGUE_MAP: out.append(LEAGUE_MAP[c])
    return out

def history_to_rows(codes: Iterable[str], seasons: Iterable[int]) -> List[Dict]:
    rows: List[Dict] = []
    with _s() as s:
        for code in _ids(codes):
            for y in seasons:
                page=1
                while True:
                    r = s.get(f"{API_BASE}/fixtures", params={"league":code,"season":y,"status":"FT","page":page}, timeout=30)
                    r.raise_for_status()
                    js = r.json(); arr = js.get("response",[])
                    for m in arr:
                        ft = (m.get("score") or {}).get("fulltime") or {}
                        rows.append({
                            "date": (m.get("fixture") or {}).get("date","")[:10],
                            "league": str(code),
                            "home": (m.get("teams") or {}).get("home",{}).get("name",""),
                            "away": (m.get("teams") or {}).get("away",{}).get("name",""),
                            "home_goals": int(ft.get("home") or 0),
                            "away_goals": int(ft.get("away") or 0),
                        })
                    if len(arr) < (js.get("paging",{}).get("per_page") or 20): break
                    page += 1; time.sleep(0.3)
    return rows

def upcoming_to_rows(codes: Iterable[str]) -> List[Dict]:
    rows: List[Dict] = []
    with _s() as s:
        for code in _ids(codes):
            r = s.get(f"{API_BASE}/fixtures", params={"league":code,"season":"2025","status":"NS"}, timeout=20)
            r.raise_for_status()
            for m in r.json().get("response",[]):
                rows.append({
                    "kickoff": (m.get("fixture") or {}).get("date",""),
                    "league": str(code),
                    "home": (m.get("teams") or {}).get("home",{}).get("name",""),
                    "away": (m.get("teams") or {}).get("away",{}).get("name",""),
                })
            time.sleep(0.3)
    return rows