"""Against-the-spread (ATS) and market-efficiency features.

From parsed game odds (scores + spreads), compute the core measures this project
studies: home margin, market error, cover outcome, and closing line value (CLV).
Spreads are HOME-team convention (negative => home favored), so:

    expected_home_margin = -spread_close
    market_error         = home_margin + spread_close   (>0 => home beat the line)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ncaa_market.config import get_config, resolve_path


def add_efficiency_features(games: pd.DataFrame) -> pd.DataFrame:
    """Add margin, market error, CLV, and cover outcomes to a games frame."""
    g = games.copy()

    g["home_margin"] = g["home_score"] - g["away_score"]
    g["market_error"] = g["home_margin"] + g["spread_close"]
    g["clv"] = g["spread_close"] - g["spread_open"]

    g["is_push"] = g["market_error"] == 0
    g["home_covered"] = np.where(
        g["market_error"] > 0,
        1.0,
        np.where(g["market_error"] < 0, 0.0, np.nan),
    )

    fav_is_home = g["favorite"].eq(g["home_team"])
    fav_is_away = g["favorite"].eq(g["away_team"])
    g["favorite_covered"] = np.where(
        fav_is_home,
        g["home_covered"],
        np.where(fav_is_away, 1.0 - g["home_covered"], np.nan),
    )

    g["cover_result"] = np.select(
        [g["is_push"], g["home_covered"] == 1.0, g["home_covered"] == 0.0],
        ["push", "home", "away"],
        default=None,
    )
    return g


def build_features(season_end: int) -> pd.DataFrame:
    """Read a staged season, add efficiency features, and save the enriched games."""
    staging = resolve_path(get_config()["paths"]["staging"])
    games = pd.read_parquet(staging / "odds" / f"odds_{season_end}.parquet")
    enriched = add_efficiency_features(games)
    out = staging / f"games_{season_end}.parquet"
    enriched.to_parquet(out, index=False)
    print(f"  features -> {out}  ({len(enriched)} games)")
    return enriched


if __name__ == "__main__":
    g = build_features(2022)
    cols = [
        "away_team",
        "home_team",
        "away_score",
        "home_score",
        "spread_close",
        "market_error",
        "cover_result",
        "favorite",
        "favorite_covered",
        "clv",
    ]
    print("\nFirst 3 games:\n", g[cols].head(3).to_string())
    evaluable = int(g["home_covered"].notna().sum())
    print(f"\nEvaluable games (has score + spread, non-push): {evaluable} of {len(g)}")
