"""Ingest SBRO NCAA basketball odds from saved HTML season pages.

SBRO encodes each game as two rows (away then home). Open/Close hold either the
point spread or the game total, separated by magnitude (smaller = spread,
larger = total). Spread sign is taken from the moneyline, not row position.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from ncaa_market.config import get_config, resolve_path

RAW_COLUMNS = ["Date", "Rot", "VH", "Team", "1st", "2nd", "Final", "Open", "Close", "ML", "2H"]


def _to_line(x) -> float:
    """SBRO line cell -> float. 'PK'/'PICK'/'EVEN' -> 0.0; 'NL'/blank/garbage -> NaN."""
    s = str(x).strip().upper()
    if s in {"PK", "PICK", "EVEN", "EV"}:
        return 0.0
    try:
        return float(s)
    except ValueError:
        return float("nan")


def _parse_date(mmdd, start_year: int, end_year: int) -> pd.Timestamp:
    """SBRO date is MM+DD with no year (1109 = Nov 9, 101 = Jan 1).

    Jul-Dec belong to the season's first calendar year; Jan-Jun the second.
    """
    s = str(mmdd).strip().split(".")[0].zfill(4)
    try:
        month, day = int(s[:2]), int(s[2:])
        year = start_year if month >= 7 else end_year
        return pd.Timestamp(year=year, month=month, day=day)
    except (ValueError, TypeError):
        return pd.NaT


def _decode_spread_total(
    away_line: np.ndarray,
    home_line: np.ndarray,
    ml_away: np.ndarray,
    ml_home: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Split Open/Close into spread (home convention) and total.

    Magnitude separates spread vs total (min/max). Sign comes from ML — not row position.
    """
    spread = np.minimum(away_line, home_line)
    total = np.maximum(away_line, home_line)
    away_fav = ml_away < ml_home
    home_fav = ml_home < ml_away
    pickem = (np.abs(ml_away - ml_home) < 1) & (spread <= 1.0)
    # Fallback: if ML is missing or equal (can't infer favorite), keep a usable
    # spread sign using SBRO row-position heuristic.
    spread_on_home_row = home_line < away_line
    row_signed = np.where(spread_on_home_row, -spread, spread)

    signed = np.where(
        pickem,
        0.0,
        np.where(away_fav, spread, np.where(home_fav, -spread, row_signed)),
    )
    return signed, total


def load_season_long(html_path: str | Path, season_end: int) -> pd.DataFrame:
    """Read one saved SBRO season page into a typed long frame (one row per team-game)."""
    start_year = season_end - 1
    path = resolve_path(html_path)
    if not path.exists():
        raise FileNotFoundError(f"SBRO HTML not found: {path}")

    raw = pd.read_html(path, flavor="lxml")[0]   # pin the parser -> reproducible
    df = raw.iloc[1:].copy()
    df.columns = RAW_COLUMNS
    df = df.reset_index(drop=True)

    df["date"] = df["Date"].apply(lambda d: _parse_date(d, start_year, season_end))
    for col in ["Rot", "1st", "2nd", "Final", "ML"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["Open", "Close", "2H"]:
        df[col] = df[col].apply(_to_line)
    df["VH"] = df["VH"].astype(str).str.strip().str.upper()
    df["Team"] = df["Team"].astype(str).str.strip()
    return df


def collapse_to_games(long_df: pd.DataFrame, season_end: int) -> pd.DataFrame:
    """Collapse the two-rows-per-game long frame into one row per game."""
    away = long_df.iloc[0::2].reset_index(drop=True)
    home = long_df.iloc[1::2].reset_index(drop=True)

    games = pd.DataFrame({
        "season": season_end,
        "date": away["date"],
        "away_team": away["Team"],
        "home_team": home["Team"],
        "away_score": away["Final"],
        "home_score": home["Final"],
        "ml_away": away["ML"],
        "ml_home": home["ML"],
        "neutral_site": ((away["VH"] == "N") | (home["VH"] == "N")).astype(int),
    })

    ml_away = away["ML"].to_numpy(dtype="float64")
    ml_home = home["ML"].to_numpy(dtype="float64")
    for stage in ["Open", "Close"]:
        spread, total = _decode_spread_total(
            away[stage].to_numpy(dtype="float64"),
            home[stage].to_numpy(dtype="float64"),
            ml_away,
            ml_home,
        )
        key = stage.lower()
        games[f"spread_{key}"] = spread
        games[f"total_{key}"] = total

    away_fav = ml_away < ml_home
    home_fav = ml_home < ml_away
    games["favorite"] = np.where(
        away_fav,
        games["away_team"],
        np.where(home_fav, games["home_team"], pd.NA),
    )
    return games


def validate_games(games: pd.DataFrame) -> None:
    """Sanity-check parsed games. Hard-fail on structural problems; report soft ones."""
    if games["away_team"].eq(games["home_team"]).any():
        raise ValueError("Found games where away_team == home_team — pairing is wrong.")
    n = len(games)
    bad_dates = int(games["date"].isna().sum())
    miss_close = int(games["spread_close"].isna().sum())
    miss_score = int(games["home_score"].isna().sum() + games["away_score"].isna().sum())
    print(
        f"  validate: {n} games | bad dates={bad_dates} | "
        f"missing closing spread={miss_close} | rows missing score={miss_score}"
    )


def save_games(games: pd.DataFrame, season_end: int) -> Path:
    """Write the parsed season to the staging layer as Parquet."""
    out_dir = resolve_path(get_config()["paths"]["staging"]) / "odds"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"odds_{season_end}.parquet"
    games.to_parquet(out_path, index=False)
    return out_path


def write_manifest(html_path: str | Path, season_end: int, source_url: str, n_games: int) -> None:
    """Record (or update) one provenance row per season in data/raw/odds/MANIFEST.md.

    Idempotent: re-ingesting a season replaces its row instead of appending a duplicate.
    """
    path = resolve_path(html_path)
    raw_dir = resolve_path(get_config()["paths"]["raw"]) / "odds"
    raw_dir.mkdir(parents=True, exist_ok=True)
    manifest = raw_dir / "MANIFEST.md"

    sha = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    today = pd.Timestamp.today().date().isoformat()
    label = f"{season_end - 1}-{str(season_end)[2:]}"

    header = (
        "# Raw odds — provenance\n\n"
        "| Season | File | Source | Downloaded | Games | SHA256 |\n"
        "|---|---|---|---|---|---|\n"
    )

    # Load any existing rows, keyed by season, so we can update in place.
    rows: dict[str, str] = {}
    if manifest.exists():
        for line in manifest.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("|") and "---" not in line and not line.startswith("| Season"):
                rows[line.split("|")[1].strip()] = line

    rows[label] = f"| {label} | {path.name} | {source_url} | {today} | {n_games} | {sha} |"

    body = "\n".join(rows[k] for k in sorted(rows)) + "\n"
    manifest.write_text(header + body, encoding="utf-8")


def ingest_season(html_path: str | Path, season_end: int, source_url: str) -> pd.DataFrame:
    """Full single-season odds ingest: load -> collapse -> validate -> save -> manifest."""
    long_df = load_season_long(html_path, season_end)
    games = collapse_to_games(long_df, season_end)
    validate_games(games)
    out_path = save_games(games, season_end)
    write_manifest(html_path, season_end, source_url, len(games))
    print(f"  saved {len(games)} games -> {out_path}")
    return games
