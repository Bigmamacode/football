from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple

@dataclass
class TeamStrength:
    attack: float
    defense: float

class PoissonUnderOverModel:
    """
    Modello Poisson indipendente: stima i gol attesi (lambda) per casa/trasferta
    a partire da forze d'attacco/difesa + vantaggio casa (home_adv).
    """
    def __init__(self, home_adv: float = 0.15):
        self.home_adv = home_adv
        self.team_strengths: Dict[str, TeamStrength] = {}
        self.global_avg_goals = 2.6  # media grezza per normalizzazione

    def fit(self, history: List[Dict]):
        """history: lista di dict con chiavi: home, away, home_goals, away_goals"""
        teams = set()
        for m in history:
            teams.add(m["home"]) ; teams.add(m["away"])

        # calcolo medie per squadra
        stats = {t: {"gf_home":0, "ga_home":0, "nh":0, "gf_away":0, "ga_away":0, "na":0} for t in teams}
        for m in history:
            h, a = m["home"], m["away"]
            gh, ga = m["home_goals"], m["away_goals"]
            stats[h]["gf_home"] += gh
            stats[h]["ga_home"] += ga
            stats[h]["nh"] += 1
            stats[a]["gf_away"] += ga
            stats[a]["ga_away"] += gh
            stats[a]["na"] += 1

        # stima attacco e difesa con smoothing
        eps = 1e-3
        for t in teams:
            nh = max(1, stats[t]["nh"]) ; na = max(1, stats[t]["na"])
            att = ((stats[t]["gf_home"] + stats[t]["gf_away"]) / (nh + na + eps)) / (self.global_avg_goals/2)
            dff = ((stats[t]["ga_home"] + stats[t]["ga_away"]) / (nh + na + eps)) / (self.global_avg_goals/2)
            # regolarizzazione lieve verso 1.0
            self.team_strengths[t] = TeamStrength(
                attack = 0.15*1.0 + 0.85*att,
                defense = 0.15*1.0 + 0.85*dff,
            )

    def expected_goals(self, home: str, away: str) -> Tuple[float,float]:
        ts_h = self.team_strengths.get(home, TeamStrength(1.0,1.0))
        ts_a = self.team_strengths.get(away, TeamStrength(1.0,1.0))
        base = self.global_avg_goals/2
        lam_home = base * ts_h.attack * (1.0/ max(1e-3, ts_a.defense)) * (1.0 + self.home_adv)
        lam_away = base * ts_a.attack * (1.0/ max(1e-3, ts_h.defense))
        return float(max(lam_home, 0.05)), float(max(lam_away, 0.05))

    def prob_under_over(self, lam_home: float, lam_away: float, line: float = 2.5) -> Tuple[float,float]:
        # distribuzione del totale gol via convoluzione di due Poisson indipendenti
        # P(T=k) dove k fino a Kmax
        Kmax = 10
        pmf_home = np.exp(-lam_home) * np.array([lam_home**k / np.math.factorial(k) for k in range(Kmax+1)])
        pmf_away = np.exp(-lam_away) * np.array([lam_away**k / np.math.factorial(k) for k in range(Kmax+1)])
        pmf_tot = np.convolve(pmf_home, pmf_away)[:Kmax+Kmax+1]
        k_cut = int(np.floor(line))  # 2 per 2.5
        p_under = float(pmf_tot[:k_cut+1].sum())
        p_over = 1.0 - p_under
        return p_under, p_over
