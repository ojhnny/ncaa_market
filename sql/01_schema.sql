-- ============================================================================
--  NCAA Market Efficiency — Star Schema (SQLite dialect, ANSI-portable)
--  ---------------------------------------------------------------------------
--  Pattern : Kimball dimensional model (one fact, conformed dimensions).
--  Grain   : fact_game = exactly ONE ROW PER GAME.
--  Notes   : Written for SQLite (the committed, clone-and-run artifact) but
--            uses standard types so it ports to PostgreSQL with minimal change.
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
--  DIMENSIONS
-- ----------------------------------------------------------------------------

-- A season is labeled by the calendar year it ENDS (2024 = the 2023-24 season).
CREATE TABLE IF NOT EXISTS dim_season (
    season_id   INTEGER PRIMARY KEY,      -- e.g., 2024
    start_year  INTEGER NOT NULL,         -- 2023
    end_year    INTEGER NOT NULL,         -- 2024
    label       TEXT    NOT NULL          -- '2023-24'
);

CREATE TABLE IF NOT EXISTS dim_conference (
    conference_id  INTEGER PRIMARY KEY,
    conference_name TEXT NOT NULL UNIQUE,  -- 'ACC', 'Big Ten', ...
    is_high_major  INTEGER NOT NULL DEFAULT 0
        CHECK (is_high_major IN (0, 1))
);

CREATE TABLE IF NOT EXISTS dim_team (
    team_id        INTEGER PRIMARY KEY,
    team_name      TEXT NOT NULL UNIQUE,   -- canonical name (crosswalk target)
    is_blue_blood  INTEGER NOT NULL DEFAULT 0
        CHECK (is_blue_blood IN (0, 1))
);

-- One row per calendar date on which games occurred.
CREATE TABLE IF NOT EXISTS dim_date (
    date_id      INTEGER PRIMARY KEY,      -- YYYYMMDD (e.g., 20240315)
    full_date    TEXT NOT NULL,            -- ISO 'YYYY-MM-DD'
    season_id    INTEGER NOT NULL REFERENCES dim_season(season_id),
    month        INTEGER NOT NULL,         -- 1-12
    day_of_week  INTEGER NOT NULL          -- 0=Mon .. 6=Sun
);

-- Reference table of weekly poll rankings (kept for traceability; the
-- as-of-game-date ranks are also denormalized onto fact_game for easy slicing).
CREATE TABLE IF NOT EXISTS ranking (
    season_id  INTEGER NOT NULL REFERENCES dim_season(season_id),
    team_id    INTEGER NOT NULL REFERENCES dim_team(team_id),
    poll_date  TEXT    NOT NULL,           -- ISO date the poll was released
    ap_rank    INTEGER,                    -- 1-25, NULL if unranked
    PRIMARY KEY (season_id, team_id, poll_date)
);

-- ----------------------------------------------------------------------------
--  FACT
--  Grain: one game. All betting/efficiency measures live here.
--  Spread convention: HOME-team spread (negative => home is favored).
--    expected_home_margin = -spread_close
--    market_error         = home_margin + spread_close   (home beat line if > 0)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_game (
    game_id              INTEGER PRIMARY KEY,
    date_id              INTEGER NOT NULL REFERENCES dim_date(date_id),
    season_id            INTEGER NOT NULL REFERENCES dim_season(season_id),

    home_team_id         INTEGER NOT NULL REFERENCES dim_team(team_id),
    away_team_id         INTEGER NOT NULL REFERENCES dim_team(team_id),
    home_conference_id   INTEGER REFERENCES dim_conference(conference_id),
    away_conference_id   INTEGER REFERENCES dim_conference(conference_id),

    neutral_site         INTEGER NOT NULL DEFAULT 0 CHECK (neutral_site IN (0,1)),
    is_postseason        INTEGER NOT NULL DEFAULT 0 CHECK (is_postseason IN (0,1)),
    game_type            TEXT NOT NULL DEFAULT 'regular'
        CHECK (game_type IN ('regular','conf_tourney','ncaa_tourney','other_postseason')),

    -- Outcome
    home_score           INTEGER,
    away_score           INTEGER,
    home_margin          INTEGER,          -- home_score - away_score

    -- Betting lines (home-team convention; negative => home favored)
    spread_open          REAL,
    spread_close         REAL,
    total_open           REAL,
    total_close          REAL,
    ml_home              INTEGER,          -- American odds
    ml_away              INTEGER,
    favorite_team_id     INTEGER REFERENCES dim_team(team_id),

    -- Derived efficiency measures (materialized for BI convenience)
    market_error         REAL,             -- home_margin + spread_close
    clv                  REAL,             -- spread_close - spread_open (line movement)
    cover_result         TEXT CHECK (cover_result IN ('home','away','push')),
    home_covered         INTEGER CHECK (home_covered IN (0,1)),     -- NULL on push
    favorite_covered     INTEGER CHECK (favorite_covered IN (0,1)), -- NULL on push / pick'em
    is_push              INTEGER NOT NULL DEFAULT 0 CHECK (is_push IN (0,1)),

    -- As-of-game-date rankings (NULL = unranked)
    home_ap_rank         INTEGER,
    away_ap_rank         INTEGER
);

-- ----------------------------------------------------------------------------
--  INDEXES — speed up the slices the analysis hits most often
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS ix_fact_season       ON fact_game(season_id);
CREATE INDEX IF NOT EXISTS ix_fact_home_team     ON fact_game(home_team_id);
CREATE INDEX IF NOT EXISTS ix_fact_away_team     ON fact_game(away_team_id);
CREATE INDEX IF NOT EXISTS ix_fact_home_conf     ON fact_game(home_conference_id);
CREATE INDEX IF NOT EXISTS ix_fact_away_conf     ON fact_game(away_conference_id);
CREATE INDEX IF NOT EXISTS ix_fact_date          ON fact_game(date_id);
CREATE INDEX IF NOT EXISTS ix_fact_postseason    ON fact_game(is_postseason);
