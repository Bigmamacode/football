from __future__ import annotations

import os, logging
from typing import List, Optional, Tuple
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

API_TITLE = "Under/Over API"
API_VERSION = "0.3.0"  # <— bump
LINE = float(os.getenv("UNDER_OVER_LINE", "2.5"))
HOME_ADV = float(os.getenv("POISSON_HOME_ADV", "0.15"))
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*").strip()

app = FastAPI(title=API_TITLE, version=API_VERSION)
allow_origins = ["*"] if FRONTEND_ORIGIN in ("", "*") else [FRONTEND_ORIGIN]
allow_credentials = False if allow_origins == ["*"] else True
app.add_middleware(CORSMiddleware, allow_origins=allow_origins, allow_credentials=allow_credentials, allow_methods=["*"], allow_headers=["*"])

log = logging.getLogger("uvicorn.error")

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

_MODEL = None
_FITTED = False

def _ensure_model():
    global _MODEL, _FITTED
    try:
        from models.poisson import PoissonUnderOverModel  # type: ignore
        from data.loader import get_history, get_mock_history  # type: ignore
    except Exception as e:
        log.exception("Import failed")
        raise RuntimeError("import_failed") from e
    if _MODEL is None:
        _MODEL = PoissonUnderOverModel(home_adv=HOME_ADV)
    if not _FITTED:
        hist = get_history()
        if not hist:
            raise RuntimeError("empty_history")
        _MODEL.fit(hist)
        # se non apprende team strength, rifitta sui mock
        try:
            meta = _MODEL.meta()
            if (meta.get("teams_att", 0) < 1) or (meta.get("teams_def", 0) < 1):
                log.warning("No team strengths from history; refitting on mock fallback")
                _MODEL.fit(get_mock_history())
        except Exception:
            pass
        _FITTED = True
        log.info("Model meta after fit: %s", getattr(_MODEL, "meta", lambda: {})())
    return _MODEL

def _get_matches():
    from data.loader import get_matches  # type: ignore
    return get_matches() or []

def _get_mock_matches():
    from data.loader import get_mock_matches  # type: ignore
    return get_mock_matches()

def _predict_pair(model, home: str, away: str, line: float) -> Tuple[float, float, float, float]:
    lam_h, lam_a = model.expected_goals(home, away)
    p_under, p_over = model.prob_under_over(lam_h, lam_a, line=line)
    return lam_h, lam_a, p_under, p_over

@app.get("/health")
def health():
    return {"ok": True, "version": API_VERSION}

@app.get("/debug/model")
def debug_model(home: str | None = Query(default=None), away: str | None = Query(default=None)):
    try:
        m = _ensure_model()
        meta = getattr(m, "meta", lambda: {"model_id":"unknown"})()
        out = {"meta": meta}
        if home and away:
            lam_h, lam_a = m.expected_goals(home, away)
            p_u, p_o = m.prob_under_over(lam_h, lam_a, LINE)
            out["pair"] = {
                "home": home, "away": away,
                "lambda_home": round(float(lam_h),3),
                "lambda_away": round(float(lam_a),3),
                "p_under": round(float(p_u),4),
                "p_over": round(float(p_o),4),
            }
        return JSONResponse(out)
    except Exception as e:
        log.exception("/debug/model failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/predictions", response_model=List[Prediction])
def predictions(force_mock: Optional[str] = Query(default=None)) -> List[Prediction]:
    fm = str(force_mock or "").strip().lower() in ("1","true","yes","on")

    try:
        model = _ensure_model()
    except Exception:
        log.exception("Model initialization/fit failed")
        raise HTTPException(status_code=500, detail="model_init_failed")

    try:
        matches = _get_mock_matches() if fm else _get_matches()
        if not matches:
            log.warning("matches empty (fm=%s), using mock fallback", fm)
            matches = _get_mock_matches()
    except Exception:
        log.exception("matches loader failed")
        raise HTTPException(status_code=500, detail="matches_loader_failed")

    out: List[Prediction] = []
    for m in matches:
        try:
            home = (m.get("home") or m.get("homeTeam") or "").strip()
            away = (m.get("away") or m.get("awayTeam") or "").strip()
            if not home or not away: continue
            lam_h, lam_a, p_u, p_o = _predict_pair(model, home, away, LINE)
            out.append(Prediction(
                league=m.get("league"), home=home, away=away, kickoff=m.get("kickoff"),
                lambda_home=round(float(lam_h),3), lambda_away=round(float(lam_a),3),
                p_under=round(float(p_u),4), p_over=round(float(p_o),4),
            ))
        except Exception:
            log.exception("Skipping bad match row: %s", m)
            continue
    return out

@app.get("/")
def root():
    return {"name": API_TITLE, "version": API_VERSION, "docs": "/docs", "health": "/health", "predictions": "/predictions"}