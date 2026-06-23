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

# Wilson (95% CI) performs better than the normal approximation at small sample sizes.
# How certain are we about the true probability of covering?
def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0: # If there are no games, then return NaN for the CI.
        return (float("nan"), float("nan"))
    p = successes / n # Calculate the proportion of successes.
    denom = 1 + z**2 / n # Calculate the denominator.
    center = (p + z**2 / (2 * n)) / denom # Calculate the center.
    margin = (z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom # Calculate the margin.
    return (center - margin, center + margin) # Return the CI.


def cover_rate(outcomes: pd.Series, label: str) -> dict:
    """Summarize a 0/1 cover series: n, rate, and Wilson CI (pushes/NaN excluded)."""
    s = outcomes.dropna() # Remove the pushes (NaNs)
    n = len(s) # Count the number of games.
    successes = int(s.sum()) # Count the number of successes [1.0 for covered, 0.0 for not covered]
    rate = successes / n if n else float("nan") # Calculate the rate.
    lo, hi = wilson_ci(successes, n) # Calculate the CI.
    return {"split": label, "n": n, "cover_rate": rate, "ci_low": lo, "ci_high": hi}

# First look at the cover rates for a given season.
def first_look(season_end: int) -> pd.DataFrame:
    staging = resolve_path(get_config()["paths"]["staging"]) # Get the staging path.
    g = pd.read_parquet(staging / f"games_{season_end}.parquet") # Read the games.

    # Identify home favorites and home underdogs.
    home_is_dog = g["favorite"].eq(g["away_team"])   
    home_is_fav = g["favorite"].eq(g["home_team"]) 

    rows = [ # Create a list of rows for the cover rates.
        cover_rate(g["favorite_covered"], "All favorites"),
        cover_rate(g["home_covered"], "All home teams"),
        cover_rate(g.loc[home_is_dog, "home_covered"], "Home underdogs"),
        cover_rate(g.loc[home_is_fav, "home_covered"], "Home favorites"),
        cover_rate(g.loc[home_is_dog, "favorite_covered"], "Road favorites"),
    ]
    out = pd.DataFrame(rows) # Create a dataframe from the rows.
    out["sig_vs_50"] = (out["ci_low"] > 0.50) | (out["ci_high"] < 0.50)   # CI excludes 50%? If the CI does not include 50%, then the cover rate is significant.
    return out # Return the dataframe.


if __name__ == "__main__":
    pd.set_option("display.float_format", lambda x: f"{x:.4f}") # Set the display format to 4 decimal places.       
    print(first_look(2022).to_string(index=False)) # Print the dataframe.           