from __future__ import annotations
from typing import Dict, Tuple, List
import math
from datetime import datetime

class PoissonUnderOverModel:
    """
    Modello Poisson con stime di attacco/difesa per squadra.
    - Stima lambda_home/away = mu * fattori_attacco * fattori_difesa_opp * home_adv
    - Smoothing di Laplace per stabilità su campioni piccoli
    - Fallback sicuri per squadre mai viste
    """
    def __init__(self, home_adv: float = 0.15, smooth_k: float = 3.0, half_life_days: int | None = 180):
        self.home_adv = float(home_adv)
        self.smooth_k = float(smooth_k)   # forza dello smoothing verso la media di lega
        self.half_life_days = half_life_days  # se None: nessun decadimento temporale
        self.mu = 2.6 / 2.0               # gol medi per team per match (inizializzazione)
        self.att: Dict[str, float] = {}
        self.defn: Dict[str, float] = {}

    # ---------- Utils ----------
    @staticmethod
    def _parse_date(dval) -> datetime | None:
        if not dval:
            return None
        # accetta "YYYY-MM-DD" o ISO con tempo
        try:
            if isinstance(dval, str):
                if len(dval) >= 10:
                    return datetime.fromisoformat(dval[:19].replace("Z",""))
        except Exception:
            return None
        return None

    def _weight(self, d: datetime | None, now: datetime) -> float:
        if self.half_life_days is None or d is None:
            return 1.0
        age_days = abs((now - d).days)
        # esponenziale con emivita (half-life)
        return math.exp(-math.log(2.0) * (age_days / max(1, self.half_life_days)))

    # ---------- Fit ----------
    def fit(self, matches: List[dict]):
        """
        matches: lista di dict con chiavi almeno:
          - 'home', 'away', 'home_goals', 'away_goals'
          - opzionale 'date' (usata per pesi temporali)
        """
        if not matches:
            # fallback: mantieni media di default
            self.mu = 2.6 / 2.0
            self.att.clear(); self.defn.clear()
            return

        now = datetime.utcnow()
        # aggregati
        gf: Dict[str, float] = {}   # goals for
        ga: Dict[str, float] = {}   # goals against
        n:  Dict[str, float] = {}   # numero partite (pesato)

        tot_goals = 0.0
        tot_matches = 0.0

        for m in matches:
            h = str(m.get("home") or m.get("homeTeam") or "").strip()
            a = str(m.get("away") or m.get("awayTeam") or "").strip()
            if not h or not a:
                continue
            try:
                hg = float(m.get("home_goals"))
                ag = float(m.get("away_goals"))
            except Exception:
                # se mancano i gol, salta
                continue

            w = self._weight(self._parse_date(m.get("date")), now)
            gf[h] = gf.get(h, 0.0) + w * hg
            ga[h] = ga.get(h, 0.0) + w * ag
            n[h]  = n.get(h, 0.0)  + w

            gf[a] = gf.get(a, 0.0) + w * ag
            ga[a] = ga.get(a, 0.0) + w * hg
            n[a]  = n.get(a, 0.0)  + w

            tot_goals += w * (hg + ag)
            tot_matches += w

        # media di lega per team per match
        league_mean_team = (tot_goals / max(1e-9, tot_matches)) / 2.0
        # se qualcosa va storto, fallback
        self.mu = float(league_mean_team) if league_mean_team > 0 else 2.6/2.0

        k = self.smooth_k
        self.att.clear()
        self.defn.clear()

        # stime per squadra con smoothing di Laplace verso la media di lega (mu)
        for team in set(list(gf.keys()) + list(ga.keys())):
            nn = n.get(team, 0.0)
            g_for = gf.get(team, 0.0)
            g_against = ga.get(team, 0.0)

            # medie osservate per partita (pesate)
            m_for = g_for / max(1e-9, nn)
            m_against = g_against / max(1e-9, nn)

            # shrink verso mu
            att = (g_for + k * self.mu) / (nn + k) / max(1e-9, self.mu)
            dfn = (g_against + k * self.mu) / (nn + k) / max(1e-9, self.mu)

            # limiti per evitare estremi irrealistici
            att = min(max(att, 0.4), 1.8)
            dfn = min(max(dfn, 0.4), 1.8)

            self.att[team] = float(att)
            self.defn[team] = float(dfn)

    # ---------- Inference ----------
    def expected_goals(self, home: str, away: str) -> Tuple[float, float]:
        # fattori (fallback a 1.0 per squadre sconosciute)
        ah = self.att.get(home, 1.0)
        dh = self.defn.get(home, 1.0)
        aa = self.att.get(away, 1.0)
        da = self.defn.get(away, 1.0)

        lam_h = self.mu * (1.0 + self.home_adv) * ah * da
        lam_a = self.mu * (1.0 - self.home_adv) * aa * dh

        # salvaguardie
        lam_h = float(max(0.05, min(lam_h, 5.0)))
        lam_a = float(max(0.05, min(lam_a, 5.0)))
        return lam_h, lam_a

    def prob_under_over(self, lam_h: float, lam_a: float, line: float = 2.5) -> Tuple[float, float]:
        lam_t = float(lam_h + lam_a)
        kmax = int(math.floor(line))
        # P(X <= kmax) per X~Poisson(lam_t)
        p_under = 0.0
        for k in range(0, kmax + 1):
            # termine Poisson
            p_under += math.exp(-lam_t) * (lam_t ** k) / math.factorial(k)
        p_under = max(0.0, min(1.0, p_under))
        return p_under, (1.0 - p_under)