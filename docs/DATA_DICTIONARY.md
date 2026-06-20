# Data Dictionary

All measures use the **home-team spread convention**: `spread_close` is the home
team's closing spread, **negative when the home team is favored**. Two identities
follow from that convention:

```
expected_home_margin = -spread_close
market_error         = home_margin + spread_close      # > 0  => home beat the line
```

## fact_game  (grain: one row per game)

| Column | Type | Description |
|--------|------|-------------|
| `game_id` | INTEGER PK | Surrogate key for the game. |
| `date_id` | INTEGER FK | → `dim_date`. YYYYMMDD. |
| `season_id` | INTEGER FK | → `dim_season`. Year the season ends (2024 = 2023-24). |
| `home_team_id` / `away_team_id` | INTEGER FK | → `dim_team`. |
| `home_conference_id` / `away_conference_id` | INTEGER FK | → `dim_conference`, captured **as of game time** (handles realignment). |
| `neutral_site` | 0/1 | 1 if played at a neutral venue. |
| `is_postseason` | 0/1 | 1 for conference/NCAA tournament & other postseason games. |
| `game_type` | TEXT | `regular` \| `conf_tourney` \| `ncaa_tourney` \| `other_postseason`. |
| `home_score` / `away_score` | INTEGER | Final score. |
| `home_margin` | INTEGER | `home_score - away_score`. |
| `spread_open` / `spread_close` | REAL | Home-team spread (negative = home favored). |
| `total_open` / `total_close` | REAL | Game total (over/under) line. |
| `ml_home` / `ml_away` | INTEGER | Moneyline (American odds). |
| `favorite_team_id` | INTEGER FK | Team favored at close (NULL on a pick'em). |
| `market_error` | REAL | `home_margin + spread_close`. Core mispricing measure. |
| `clv` | REAL | `spread_close - spread_open`. Line movement / closing-line value. |
| `cover_result` | TEXT | `home` \| `away` \| `push` — which side covered. |
| `home_covered` | 0/1 | 1 if home covered the spread; NULL on push. |
| `favorite_covered` | 0/1 | 1 if the favorite covered; NULL on push / pick'em. |
| `is_push` | 0/1 | 1 if the margin landed exactly on the spread. |
| `home_ap_rank` / `away_ap_rank` | INTEGER | AP rank (1–25) as of game date; NULL if unranked. |

## dim_team
| Column | Type | Description |
|--------|------|-------------|
| `team_id` | INTEGER PK | Surrogate key. |
| `team_name` | TEXT | Canonical team name (crosswalk target). |
| `is_blue_blood` | 0/1 | Flags Duke, Kentucky, UNC, Kansas, UCLA, Indiana (configurable). |

## dim_conference
| Column | Type | Description |
|--------|------|-------------|
| `conference_id` | INTEGER PK | Surrogate key. |
| `conference_name` | TEXT | e.g., `ACC`, `Big Ten`. |
| `is_high_major` | 0/1 | 1 for the power conferences. |

## dim_season
| Column | Type | Description |
|--------|------|-------------|
| `season_id` | INTEGER PK | Year the season ends. |
| `start_year` / `end_year` | INTEGER | Calendar span. |
| `label` | TEXT | e.g., `2023-24`. |

## dim_date
| Column | Type | Description |
|--------|------|-------------|
| `date_id` | INTEGER PK | YYYYMMDD. |
| `full_date` | TEXT | ISO `YYYY-MM-DD`. |
| `season_id` | INTEGER FK | → `dim_season`. |
| `month` | INTEGER | 1–12 (enables "by month" market-accuracy analysis). |
| `day_of_week` | INTEGER | 0=Mon … 6=Sun. |

## ranking  (reference)
| Column | Type | Description |
|--------|------|-------------|
| `season_id` | INTEGER FK | → `dim_season`. |
| `team_id` | INTEGER FK | → `dim_team`. |
| `poll_date` | TEXT | ISO date the poll was released. |
| `ap_rank` | INTEGER | 1–25, NULL if unranked. |
