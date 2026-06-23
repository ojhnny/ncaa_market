"""Stage 1 — Ingestion. Download/scrape raw odds, results, and rankings into data/raw/."""

from ncaa_market.ingest.odds import collapse_to_games, ingest_season, load_season_long

__all__ = ["collapse_to_games", "ingest_season", "load_season_long"]
