$path = "C:\Users\Utente\Desktop\calcio-under-over-mvp\backend\main.py"
$code = @'
from __future__ import annotations

import os
import logging
from typing import List, Optional, Tuple

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# --- Config ---
API_TITLE = "Under/Over API"
API_VERSION = "0.2.0"
LINE = float(os.getenv("UNDER_OVER_LINE", "2.5"))
HOME_ADV = float(os.getenv("POISSON_HOME_ADV", "0.15"))
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*").strip()

# --- Local imports ---
from data.loader import get_history, get_matches  # type: ignore
from models.poisson import PoissonUnderOverModel  # type: ignore

# --- App & CORS ---
app = FastAPI(title=API_TITLE, version=API_VERSION)
allow_origins = ["*"] if FRONTEND_ORIGIN in ("", "*") else [FRONTEND_ORIGIN]
allow_credentials = False if allow_origins == ["*"] else True

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

log = logging.getLogger("uvicorn.error")

# --- Schemi ---
class Match(BaseModel):
    league: Optional[str] = Field(default=None)
    home: str
    away: str
    kickoff: Optional[str] = Field(default=None)

class Prediction(BaseModel):
    league: Optional[str] = None
    home: str
    away: str
    kickoff: Optional[str] = None
    lambda_home: float
    lambda_away: float
    line: float = LINE
    p_under: float
    p_over: float

# --- Stato/modello (lazy fit) ---
_MODEL: Optional[PoissonUnderOverModel] = None
_FITTED: bool = False

def _ensure_model() -> PoissonUnderOverModel:
    global _MODEL, _FITTED
    if _MODEL is None:
        _MODEL = PoissonUnderOverModel(home_adv=HOME_ADV)
    if not _FITTED:
        history = get_history()
        _MODEL.fit(history)
        _FITTED = True
        log.info("Poisson fitted on %d matches (HOME_ADV=%s)", len(history), HOME_ADV)
    return _MODEL

def _predict_pair(
    model: PoissonUnderOverModel, home: str, away: str, line: float
) -> Tuple[float, float, float, float]:
    """Ritorna (lambda_home, lambda_away, p_under, p_over) per una coppia home/away."""
    lam_h, lam_a = model.expected_goals(home, away)
    p_under, p_over = model.prob_under_over(lam_h, lam_a, line=line)
    return lam_h, lam_a, p_under, p_over

# --- Routes ---
@app.get("/health")
def health():
    return {"ok": True, "version": API_VERSION}

@app.get("/predictions", response_model=List[Prediction])
def predictions() -> List[Prediction]:
    model = _ensure_model()
    matches = get_matches()
    out: List[Prediction] = []
    for m in matches:
        home = (m.get("home") or m.get("homeTeam") or "").strip()
        away = (m.get("away") or m.get("awayTeam") or "").strip()
        if not home or not away:
            continue
        lam_h, lam_a, p_u, p_o = _predict_pair(model, home, away, LINE)
        out.append(Prediction(
            league=m.get("league"),
            home=home,
            away=away,
            kickoff=m.get("kickoff"),
            lambda_home=round(float(lam_h), 3),
            lambda_away=round(float(lam_a), 3),
            p_under=round(float(p_u), 4),
            p_over=round(float(p_o), 4),
        ))
    return out

@app.post("/predict", response_model=Prediction)
def predict(match: Match) -> Prediction:
    model = _ensure_model()
    lam_h, lam_a, p_u, p_o = _predict_pair(model, match.home, match.away, LINE)
    return Prediction(
        league=match.league,
        home=match.home,
        away=match.away,
        kickoff=match.kickoff,
        lambda_home=round(float(lam_h), 3),
        lambda_away=round(float(lam_a), 3),
        p_under=round(float(p_u), 4),
        p_over=round(float(p_o), 4),
    )

@app.get("/")
def root():
    return {
        "name": API_TITLE,
        "version": API_VERSION,
        "docs": "/docs",
        "health": "/health",
        "predictions": "/predictions",
    }
'@
[System.IO.File]::WriteAllText($path, $code, [System.Text.UTF8Encoding]::new($false))
