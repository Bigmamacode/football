from __future__ import annotations
from typing import List, Dict
from datetime import datetime, timedelta

# ===== MOCK DATA =====
# In produzione, sostituisci con chiamate alle API.

def get_mock_history() -> List[Dict]:
    # Storico ultra-semplificato per poche squadre, ultimi match
    return [
        {"date": "2025-08-01", "home": "Milan", "away": "Inter", "home_goals": 1, "away_goals": 2},
        {"date": "2025-08-02", "home": "Juventus", "away": "Roma", "home_goals": 2, "away_goals": 1},
        {"date": "2025-08-03", "home": "Napoli", "away": "Lazio", "home_goals": 3, "away_goals": 1},
        {"date": "2025-08-04", "home": "Inter", "away": "Juventus", "home_goals": 1, "away_goals": 1},
        {"date": "2025-08-05", "home": "Roma", "away": "Napoli", "home_goals": 0, "away_goals": 2},
        {"date": "2025-08-06", "home": "Lazio", "away": "Milan", "home_goals": 2, "away_goals": 2},
        {"date": "2025-08-07", "home": "Milan", "away": "Juventus", "home_goals": 1, "away_goals": 0},
        {"date": "2025-08-08", "home": "Inter", "away": "Napoli", "home_goals": 2, "away_goals": 2},
    ]

def get_mock_matches() -> List[Dict]:
    today = datetime.utcnow().date()
    return [
        {"kickoff": str(datetime.combine(today + timedelta(days=1), datetime.min.time())), "home": "Milan", "away": "Roma", "league": "Serie A"},
        {"kickoff": str(datetime.combine(today + timedelta(days=1), datetime.min.time())), "home": "Juventus", "away": "Lazio", "league": "Serie A"},
        {"kickoff": str(datetime.combine(today + timedelta(days=2), datetime.min.time())), "home": "Inter", "away": "Napoli", "league": "Serie A"},
    ]

def get_history() -> List[Dict]:
    return get_mock_history()

def get_matches() -> List[Dict]:
    return get_mock_matches()
