"""First-pass cover-rate analysis.

Do teams/situations cover at the rate an efficient market implies? Two benchmarks:
  * 0.5000  -> unbiased line (the market's forecast is right on average)
  * 0.5238  -> break-even after the standard -110 vig (could you profit?)

Each rate comes with a Wilson 95% confidence interval, which is the honest way to
say how sure we are at this sample size
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ncaa_market.config import get_config, resolve_path


def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a binomial proportion (better than normal at small n)."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = (z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
    return (center - margin, center + margin)


def cover_rate(outcomes: pd.Series, label: str) -> dict:
    """Summarize a 0/1 cover series: n, rate, and Wilson CI (pushes/NaN excluded)."""
    s = outcomes.dropna()
    n = len(s)
    successes = int(s.sum())
    rate = successes / n if n else float("nan")
    lo, hi = wilson_ci(successes, n)
    return {"split": label, "n": n, "cover_rate": rate, "ci_low": lo, "ci_high": hi}


def first_look(season_end: int) -> pd.DataFrame:
    staging = resolve_path(get_config()["paths"]["staging"])
    g = pd.read_parquet(staging / f"games_{season_end}.parquet")

    home_is_dog = g["favorite"].eq(g["away_team"])
    home_is_fav = g["favorite"].eq(g["home_team"])

    rows = [
        cover_rate(g["favorite_covered"], "All favorites"),
        cover_rate(g["home_covered"], "All home teams"),
        cover_rate(g.loc[home_is_dog, "home_covered"], "Home underdogs"),
        cover_rate(g.loc[home_is_fav, "home_covered"], "Home favorites"),
        cover_rate(g.loc[home_is_dog, "favorite_covered"], "Road favorites"),
    ]
    out = pd.DataFrame(rows)
    # True when the Wilson CI excludes 50% (statistically different from unbiased).
    out["sig_vs_50"] = (out["ci_low"] > 0.50) | (out["ci_high"] < 0.50)
    return out


if __name__ == "__main__":
    pd.set_option("display.float_format", lambda x: f"{x:.4f}")
    print(first_look(2022).to_string(index=False))
