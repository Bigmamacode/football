from __future__ import annotations
from typing import Dict, Tuple, List, Optional
import math, re, unicodedata
from datetime import datetime

class PoissonUnderOverModel:
    """Team-strength Poisson con:
       - normalizzazione nomi squadra (accenti/suffix/punteggiatura)
       - medie per LEGA (fallback migliore per squadre non viste)
       - att/def per squadra con smoothing"""
    MODEL_ID = "team-strength-v2"

    def __init__(self, home_adv: float = 0.15, smooth_k: float = 3.0, half_life_days: int | None = 180):
        self.home_adv = float(home_adv)
        self.smooth_k = float(smooth_k)
        self.half_life_days = half_life_days
        self.mu = 2.6 / 2.0                    # media globale per team
        self.mu_by_league: Dict[str, float] = {}  # media per LEGA (es. "SA","PL"...)
        self.att: Dict[str, float] = {}        # strength attacco per team norm
        self.defn: Dict[str, float] = {}       # strength difesa per team norm

    # ---------- Normalizzazione ----------
    _STOP = {"fc","ac","cf","club","calcio","u19","u20","u21","women","ladies","the"}
    _SPACES = re.compile(r"\s+")
    _PUNCT  = re.compile(r"[^a-z0-9 ]+")

    @classmethod
    def _norm(cls, name: str) -> str:
        if not name: return ""
        s = unicodedata.normalize("NFKD", str(name))
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        s = s.lower()
        s = cls._PUNCT.sub(" ", s)
        toks = [t for t in cls._SPACES.sub(" ", s).strip().split(" ") if t and t not in cls._STOP]
        return " ".join(toks)

    @staticmethod
    def _parse_date(dval) -> datetime | None:
        if not dval: return None
        try:
            if isinstance(dval, str) and len(dval) >= 10:
                return datetime.fromisoformat(dval[:19].replace("Z",""))
        except Exception:
            return None
        return None

    def _weight(self, d: datetime | None, now: datetime) -> float:
        if self.half_life_days is None or d is None: return 1.0
        age_days = abs((now - d).days)
        return math.exp(-math.log(2.0) * (age_days / max(1, self.half_life_days)))

    # ---------- Fit ----------
    def fit(self, matches: List[dict]):
        if not matches:
            self.mu = 2.6/2.0
            self.mu_by_league.clear()
            self.att.clear(); self.defn.clear()
            return

        now = datetime.utcnow()
        gf: Dict[str, float] = {}
        ga: Dict[str, float] = {}
        n:  Dict[str, float] = {}
        # aggregati per LEGA
        g_sum_league: Dict[str, float] = {}
        n_sum_league: Dict[str, float] = {}

        tot_goals = 0.0
        tot_matches = 0.0

        for m in matches:
            league = str(m.get("league") or "").strip()
            h_raw = m.get("home") or m.get("homeTeam") or ""
            a_raw = m.get("away") or m.get("awayTeam") or ""
            h = self._norm(h_raw); a = self._norm(a_raw)
            if not h or not a: continue

            try:
                hg = float(m.get("home_goals"))
                ag = float(m.get("away_goals"))
            except Exception:
                continue

            w = self._weight(self._parse_date(m.get("date")), now)
            # team agg
            gf[h] = gf.get(h, 0.0) + w * hg
            ga[h] = ga.get(h, 0.0) + w * ag
            n[h]  = n.get(h, 0.0)  + w

            gf[a] = gf.get(a, 0.0) + w * ag
            ga[a] = ga.get(a, 0.0) + w * hg
            n[a]  = n.get(a, 0.0)  + w

            # league agg (per team per match, quindi /2 più avanti)
            g_sum_league[league] = g_sum_league.get(league, 0.0) + w * (hg + ag)
            n_sum_league[league] = n_sum_league.get(league, 0.0) + w

            tot_goals   += w * (hg + ag)
            tot_matches += w

        # medie
        league_mean_team = (tot_goals / max(1e-9, tot_matches)) / 2.0
        self.mu = float(league_mean_team) if league_mean_team > 0 else 2.6/2.0

        self.mu_by_league = {}
        for lg, gsum in g_sum_league.items():
            mu_l = (gsum / max(1e-9, n_sum_league.get(lg, 0.0))) / 2.0
            if mu_l > 0:
                self.mu_by_league[lg] = float(mu_l)

        # strength per squadra (smoothing verso mu di lega se disponibile)
        k = float(self.smooth_k)
        self.att.clear(); self.defn.clear()
        teams = set(list(gf.keys()) + list(ga.keys()))
        for t in teams:
            nn = n.get(t, 0.0)
            g_for = gf.get(t, 0.0)
            g_against = ga.get(t, 0.0)

            # usa mu globale per lo shrink (fa da “ancora” stabile); il fallback a livello lega avviene in expected_goals
            att = (g_for + k * self.mu) / (nn + k) / max(1e-9, self.mu)
            dfn = (g_against + k * self.mu) / (nn + k) / max(1e-9, self.mu)

            att = min(max(att, 0.4), 1.8)
            dfn = min(max(dfn, 0.4), 1.8)
            self.att[t]  = float(att)
            self.defn[t] = float(dfn)

    # ---------- Inference ----------
    def expected_goals(self, home: str, away: str, league: Optional[str] = None) -> Tuple[float, float]:
        h = self._norm(home); a = self._norm(away)
        base_mu = self.mu_by_league.get(str(league or ""), self.mu)

        ah = self.att.get(h, 1.0)
        dh = self.defn.get(h, 1.0)
        aa = self.att.get(a, 1.0)
        da = self.defn.get(a, 1.0)

        lam_h = base_mu * (1.0 + self.home_adv) * ah * da
        lam_a = base_mu * (1.0 - self.home_adv) * aa * dh

        lam_h = float(max(0.05, min(lam_h, 5.0)))
        lam_a = float(max(0.05, min(lam_a, 5.0)))
        return lam_h, lam_a

    def prob_under_over(self, lam_h: float, lam_a: float, line: float = 2.5) -> Tuple[float, float]:
        lam_t = float(lam_h + lam_a)
        kmax = int(math.floor(line))
        p_under = 0.0
        for k in range(0, kmax + 1):
            p_under += math.exp(-lam_t) * (lam_t**k) / math.factorial(k)
        p_under = max(0.0, min(1.0, p_under))
        return p_under, (1.0 - p_under)

    def meta(self) -> dict:
        return {
            "model_id": self.MODEL_ID,
            "mu": self.mu,
            "leagues": len(self.mu_by_league),
            "home_adv": self.home_adv,
            "teams_att": len(self.att),
            "teams_def": len(self.defn),
        }