# backend/main.py
from __future__ import annotations

import os
import logging
from typing import List, Optional, Tuple

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# -------- Config da ENV --------
API_TITLE = "Under/Over API"
API_VERSION = "0.2.0"

# linea Under/Over usata per le probabilità
LINE = float(os.getenv("UNDER_OVER_LINE", "2.5"))
# vantaggio campo del modello Poisson (0.10–0.25 tipico)
HOME_ADV = float(os.getenv("POISSON_HOME_ADV", "0.15"))

# CORS: origin del frontend (metti esattamente l’URL del frontend se vuoi restringere)
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*").strip()

# -------- Import locali (loader + modello) --------
# Il loader fornisce storico e prossime partite (API reale o mock con fallback)
from data.loader import get_history, get_matches  # type: ignore

# Modello Poisson dell’MVP (attacco/difesa per squadra + campo)
from models.poisson import PoissonUnderOverModel  # type: ignore

# -------- App & CORS --------
app = FastAPI(title=API_TITLE, version=API_VERSION)

allow_origins = ["*"] if FRONTEND_ORIGIN in ("*", "") else [FRONTEND_ORIGIN]
allow_credentials = False if allow_origins == ["*"] else True

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

log = logging.getLogger("uvicorn.error")

# -------- Pydantic Schemas --------
class Match(BaseModel):
    league: Optional[str] = Field(default=None, description="Codice lega o nome")
    home: str
    away: str
    kickoff: Optional[str] = Field(default=None, description="ISO datetime se disponibile")

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

# -------- Stato globale (lazy) --------
_MODEL: Optional[PoissonUnderOverModel] = None
_FITTED: bool = False

def _ensure_model() -> PoissonUnderOverModel:
    """Crea e fitta il modello alla prima richiesta, con storico da loader."""
    global _MODEL, _FITTED
    if _MODEL is None:
        _MODEL = PoissonUnderOverModel(home_adv=HOME_ADV)
    if not _FITTED:
        history = get_history()  # può usare API reali se è impostata la chiave; altrimenti mock
        _MODEL.fit(history)
        _FITTED = True
        log.info("Poisson model fitted on %d matches (HOME_ADV=%s)", len(history), HOME_ADV)
    return _MODEL

def _predict_pair(model: PoissonUnderOverModel, home: str, away: str, line: float) -> Tuple[float, float]()
