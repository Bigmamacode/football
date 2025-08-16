from __future__ import annotations
from typing import Dict, Tuple, List, Optional
import math, re, unicodedata
from datetime import datetime

class PoissonUnderOverModel:
    """Team-strength v3: chiave primaria per ID squadra, fallback a nome normalizzato; baselines per LEGA."""
    MODEL_ID = "team-strength-v3"

    def __init__(self, home_adv: float = 0.15, smooth_k: float = 3.0, half_life_days: Optional[int] = 180):
        self.home_adv = float(home_adv)
        self.smooth_k = float(smooth_k)
        self.half_life_days = half_life_days
        self.mu = 2.6 / 2.0
        self.mu_by_league: Dict[str, float] = {}
        self.att: Dict[str, float] = {}
        self.defn: Dict[str, float] = {}

    # --- normalizzazione nomi (fallback) ---
    _STOP = {"fc","ac","cf","club","calcio","u19","u20","u21","women","ladies","the"}
    _SPACES = re.compile(r"\s+")
    _PUNCT  = re.compile(r"[^a-z0-9 ]+")
    @classmethod
    def _norm(cls, name: str) -> str:
        if not name: return ""
        s = unicodedata.normalize("NFKD", str(name))
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        s = cls._PUNCT.sub(" ", s.lower())
        toks = [t for t in cls._SPACES.sub(" ", s).strip().split(" ") if t and t not in cls._STOP]
        return " ".join(toks)

    @staticmethod
    def _parse_date(dval) -> Optional[datetime]:
        if not dval: return None
        try:
            if isinstance(dval, str) and len(dval) >= 10:
                return datetime.fromisoformat(dval[:19].replace("Z",""))
        except Exception:
            return None
        return None

    def _weight(self, d: Optional[datetime], now: datetime) -> float:
        if self.half_life_days is None or d is None: return 1.0
        age_days = abs((now - d).days)
        return math.exp(-math.log(2.0) * (age_days / max(1, self.half_life_days)))

    @staticmethod
    def _tkey(name: str, team_id: Optional[int]) -> str:
        """Preferisci ID; fallback al nome normalizzato."""
        if team_id is not None:
            return f"id:{int(team_id)}"
        return f"name:{PoissonUnderOverModel._norm(name)}"

    # --- fit ---
    def fit(self, matches: List[dict]):
        self.att.clear(); self.defn.clear(); self.mu_by_league.clear()
        if not matches:
            self.mu = 2.6/2.0
            return

        now = datetime.utcnow()
        gf: Dict[str, float] = {}; ga: Dict[str, float] = {}; n: Dict[str, float] = {}
        g_sum_league: Dict[str, float] = {}; n_sum_league: Dict[str, float] = {}
        tot_goals = 0.0; tot_matches = 0.0

        for m in matches:
            lg = str(m.get("league") or "").strip()
            hname = m.get("home") or m.get("homeTeam") or ""
            aname = m.get("away") or m.get("awayTeam") or ""
            hid   = m.get("home_id"); aid = m.get("away_id")
            hk = self._tkey(hname, hid); ak = self._tkey(aname, aid)
            if not hk or not ak: continue
            try:
                hg = float(m.get("home_goals")); ag = float(m.get("away_goals"))
            except Exception:
                continue
            w = self._weight(self._parse_date(m.get("date")), now)
            gf[hk] = gf.get(hk, 0.0) + w*hg; ga[hk] = ga.get(hk, 0.0) + w*ag; n[hk] = n.get(hk, 0.0) + w
            gf[ak] = gf.get(ak, 0.0) + w*ag; ga[ak] = ga.get(ak, 0.0) + w*hg; n[ak] = n.get(ak, 0.0) + w
            g_sum_league[lg] = g_sum_league.get(lg, 0.0) + w*(hg+ag)
            n_sum_league[lg] = n_sum_league.get(lg, 0.0) + w
            tot_goals += w*(hg+ag); tot_matches += w

        self.mu = float(((tot_goals / max(1e-9, tot_matches)) / 2.0)) if tot_matches > 0 else 1.3
        for lg, gsum in g_sum_league.items():
            mu_l = (gsum / max(1e-9, n_sum_league.get(lg, 0.0))) / 2.0
            if mu_l > 0: self.mu_by_league[lg] = float(mu_l)

        k = float(self.smooth_k)
        for t in set(list(gf.keys()) + list(ga.keys())):
            nn = n.get(t, 0.0); g_for = gf.get(t, 0.0); g_against = ga.get(t, 0.0)
            att = (g_for + k*self.mu) / (nn + k) / max(1e-9, self.mu)
            dfn = (g_against + k*self.mu) / (nn + k) / max(1e-9, self.mu)
            self.att[t]  = float(min(max(att, 0.4), 1.8))
            self.defn[t] = float(min(max(dfn, 0.4), 1.8))

    # --- inference ---
    def expected_goals(self, home: str, away: str, league: Optional[str] = None,
                       home_id: Optional[int] = None, away_id: Optional[int] = None) -> Tuple[float, float]:
        hk = self._tkey(home, home_id); ak = self._tkey(away, away_id)
        base_mu = self.mu_by_league.get(str(league or ""), self.mu)
        ah = self.att.get(hk, 1.0); dh = self.defn.get(hk, 1.0)
        aa = self.att.get(ak, 1.0); da = self.defn.get(ak, 1.0)
        lam_h = base_mu * (1.0 + self.home_adv) * ah * da
        lam_a = base_mu * (1.0 - self.home_adv) * aa * dh
        return float(max(0.05, min(lam_h, 5.0))), float(max(0.05, min(lam_a, 5.0)))

    def prob_under_over(self, lam_h: float, lam_a: float, line: float = 2.5):
        lam_t = float(lam_h + lam_a); kmax = int(math.floor(line))
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