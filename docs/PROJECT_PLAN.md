# Project Plan — NCAA Basketball Market Efficiency Analysis

## Core question
Do NCAA men's basketball betting markets efficiently incorporate available
information into prices, or do recurring, exploitable pricing inefficiencies
exist? This is a **market-efficiency study, not a game-prediction model.**

## Guiding principles (what makes this rigorous, not generic)

1. **50% is not the benchmark — the vig is.** Spread bets priced at −110 require a
   **52.38%** win rate to break even. We test two distinct questions separately:
   - *Unbiasedness* — is the spread a correct forecast? (cover rate = 50.0%, mean
     market error = 0)
   - *Exploitability* — can a simple rule beat the vig? (cover rate > 52.38%)
2. **Closing Line Value (CLV) is the professional efficiency metric.** Using both
   opening and closing spreads, we measure line movement and whether the opening
   line is systematically beatable.
3. **Guard against data-mining.** Slicing many groups inflates false positives, so we
   apply **Benjamini–Hochberg FDR** correction and validate every "profitable angle"
   **out-of-sample** (discover on 2008–2017, confirm on 2018–2024).
4. **Report effect sizes + confidence intervals, never bare p-values.** Market edges
   are tiny; honesty about uncertainty is the credibility signal.

## Data sources (free / public)
| Domain | Source | Notes |
|--------|--------|-------|
| Odds (open/close spread, total, ML) | Sportsbook Reviews Online archives | Per-season spreadsheets, NCAAB back to 2007–08 |
| Results, scores, conferences | Sports Reference (CBB) / Barttorvik | Scraped politely (~20 req/min limit) |
| AP / Coaches poll rankings | Sports Reference | Weekly snapshots |

**Key ETL challenge:** the two sources name teams differently, so we build a
**team-name crosswalk dimension** (fuzzy match + curated aliases). **Known bias:**
odds coverage skews to high-major games — disclosed in the report's limitations.

## Architecture
Medallion layering (`raw → staging → marts`) with a **Kimball star schema** at the
gold layer: `fact_game` (grain = one game) + `dim_team`, `dim_conference`,
`dim_date`, `dim_season`, and a `ranking` reference table. Database: **SQLite**
(committed, clone-and-run); DDL is ANSI-portable to PostgreSQL. Power BI/Excel
consume flat CSV/Parquet mart exports.

## Key metrics
- **ATS result** — favorite covered / underdog covered / push (pushes excluded from
  cover-rate denominators).
- **Market error** = `home_margin + spread_close` (signed; >0 means home beat the line).
- **Cover rate** = covers / (games − pushes), compared vs 0.50 and vs 0.5238.
- **CLV** = `spread_close − spread_open`.
- **ROI** — flat $100/bet with −110 cost, reported with bootstrap CI, drawdown, and
  an out-of-sample split.

## Statistical methods
- Wilson confidence intervals for cover rates.
- Binomial / z-tests vs 0.50 and 0.5238; t-tests / bootstrap for market error.
- Benjamini–Hochberg FDR across each test family.
- OLS (`market_error ~ ...`) and logistic (`cover ~ ...`) regression on ranking,
  conference, home, spread size, month, neutral site; robust SEs clustered by season.
- Temporal trend regression to test whether efficiency has improved over time.

## Research questions answered
Team (overpricing of ranked/blue-blood/public teams), Conference (over/under-valued
conferences), Situational (home dogs, road favorites, neutral sites), Temporal
(is efficiency improving?), and Market Behavior (spread size, postseason vs regular).

## Deliverables
- **GitHub repo** — SQL DDL, Python ETL package, analysis notebooks, tests, CI, docs.
- **Excel** executive workbook — KPIs, pivots, scenario slicers.
- **Power BI** 4-page dashboard — Executive Summary, Conference, Team explorer,
  Market Inefficiencies (model + DAX library + build guide).
- **Research report** (5–10 pp.) — methodology, findings, significance, business
  implications, limitations.

## Phases
| Phase | Output |
|-------|--------|
| 0 | Foundation: repo, package, config, SQL schema, docs, CI |
| 1 | Ingestion: odds + results + rankings → raw (prove one season first) |
| 2 | Clean & reconcile: team crosswalk, validation, join → staging |
| 3 | Features & load: ATS / market error / flags → star schema |
| 4 | Statistical analysis + notebooks |
| 5 | Reporting marts (CSV/Parquet) |
| 6 | Excel + Power BI + written report |
| 7 | Polish: tests, CI green, README screenshots, ship |
