# Data layers

This project uses a **medallion architecture**: data flows in one direction through
three layers, and each layer is reproducible from the one before it. None of the
actual data files are committed to Git — only this documentation and per-layer
manifests. Run the pipeline to regenerate everything from source.

| Layer | Folder | Contents | Produced by |
|-------|--------|----------|-------------|
| 🥉 **Bronze / raw** | `data/raw/` | Immutable source files exactly as downloaded (season odds spreadsheets, scraped results/rankings). Never edited by hand. | `src/ncaa_market/ingest/` |
| 🥈 **Silver / staging** | `data/staging/` | Cleaned, typed, deduplicated, and reconciled tables. Team names crosswalked; odds joined to results. | `src/ncaa_market/clean/` |
| 🥇 **Gold / marts** | `data/marts/` | Analysis-ready **star schema** (`fact_game` + dimensions) plus flat CSV/Parquet exports consumed by Excel and Power BI. | `src/ncaa_market/features/`, `load/`, `report/` |

## Provenance

Each raw download is recorded in `data/raw/MANIFEST.md` with its source URL, the
season it covers, the download date, and a checksum. This means anyone can verify
exactly where the data came from and reproduce the bronze layer — the gold standard
for analytical credibility.

## Sources (free / public)

- **Betting odds** (open & close spread, total, moneyline): Sportsbook Reviews Online
  historical odds archives (per-season spreadsheets, NCAA basketball back to 2007–08).
- **Game results, scores, conferences, schedules**: Sports Reference / College Basketball
  Reference and/or Barttorvik.
- **AP / Coaches poll rankings** (weekly): Sports Reference poll pages.
