from __future__ import annotations
from typing import Dict, Tuple, List
import math

class PoissonUnderOverModel:
    def __init__(self, home_adv: float = 0.15):
        self.home_adv = float(home_adv)
        self.global_mean = 2.6

    def fit(self, matches: List[dict]):
        if not matches:
            self.global_mean = 2.6
            return
        totals = [int(m["home_goals"]) + int(m["away_goals"]) for m in matches if "home_goals" in m and "away_goals" in m]
        self.global_mean = float(sum(totals) / max(1,len(totals))) if totals else 2.6

    def expected_goals(self, home: str, away: str) -> Tuple[float, float]:
        base = max(0.2, self.global_mean / 2.0)
        lam_h = base * (1 + self.home_adv)
        lam_a = base * (1 - self.home_adv)
        return float(lam_h), float(lam_a)

    def prob_under_over(self, lam_h: float, lam_a: float, line: float = 2.5):
        lam_t = lam_h + lam_a
        kmax = int(math.floor(line))
        p_under = sum(math.exp(-lam_t) * (lam_t**k) / math.factorial(k) for k in range(kmax+1))
        p_under = float(max(0.0, min(1.0, p_under)))
        return p_under, float(1.0 - p_under)