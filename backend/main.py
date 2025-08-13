from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict

from models.poisson import PoissonUnderOverModel
from data.loader import get_history, get_matches

app = FastAPI(title="Under/Over API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Prediction(BaseModel):
    home: str
    away: str
    league: str
    kickoff: str
    lambda_home: float
    lambda_away: float
    under25: float
    over25: float

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/predictions", response_model=List[Prediction])
def predictions():
    history = get_history()
    matches = get_matches()

    model = PoissonUnderOverModel(home_adv=0.15)
    model.fit(history)

    out: List[Dict] = []
    for m in matches:
        lam_h, lam_a = model.expected_goals(m["home"], m["away"])
        pu, po = model.prob_under_over(lam_h, lam_a, line=2.5)
        out.append({
            "home": m["home"],
            "away": m["away"],
            "league": m.get("league",""),
            "kickoff": m["kickoff"],
            "lambda_home": round(lam_h,3),
            "lambda_away": round(lam_a,3),
            "under25": round(pu,4),
            "over25": round(po,4),
        })
    return out
