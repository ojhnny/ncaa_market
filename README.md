# 🏀 NCAA Basketball Market Efficiency Analysis

**Do betting markets price NCAA men's basketball efficiently — or do recurring,
exploitable mispricings exist?** This project analyzes **17 seasons (2008–2024)** of
game results and betting lines to find out, combining a SQL data model, a Python ETL
pipeline, rigorous statistics, and executive Excel + Power BI reporting.

> This is a **market-research / efficiency study, not a game-prediction model.** The
> goal is to *measure and explain mispricing*, with the statistical honesty to say
> when an apparent edge is just noise.

<!-- Badges (wire up once CI is live) -->
![CI](https://img.shields.io/badge/CI-pending-lightgrey)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🔑 Headline findings
> _Filled in at Phase 7 once the analysis runs end-to-end. Each claim will carry a
> confidence interval and an out-of-sample check — no bare p-values._

- _TBD: Are highly ranked teams systematically overpriced?_
- _TBD: Which conferences are most mispriced, and by how much?_
- _TBD: Are home underdogs undervalued after accounting for the vig?_
- _TBD: Has market efficiency improved over time?_

## 📊 Dashboards
> _Power BI and Excel screenshots added at Phase 7._

---

## Why this analysis is done right (and most aren't)

1. **50% is not the benchmark — the vig is.** At −110 odds you must win **52.38%** to
   break even, so we test *unbiasedness* (cover = 50%) and *exploitability*
   (cover > 52.38%) as **separate** questions.
2. **Closing Line Value.** Using opening **and** closing spreads, we measure line
   movement — the professional's efficiency signal.
3. **No data-mining.** Benjamini–Hochberg FDR correction across many slices, plus
   **out-of-sample validation** (discover 2008–2017, confirm 2018–2024).
4. **Uncertainty up front.** Effect sizes and confidence intervals on every claim.

## 🧱 Architecture

```
Sources (free)                ETL (Python)              Model (SQL)        BI
─────────────                 ────────────              ───────────        ──
Sportsbook Reviews  ─┐                                 ┌ fact_game        Excel
Sports Reference    ─┼─► raw ─► staging ─► marts ─────►┤ dim_team   ─────► Power BI
AP/Coaches polls    ─┘   (bronze) (silver) (gold)      └ dim_*            Report
```

Medallion layering with a **Kimball star schema** at the gold layer. Database is
**SQLite** (clone-and-run); DDL is ANSI-portable to PostgreSQL.

## 🛠️ Tech stack
| Area | Tools |
|------|-------|
| ETL | Python · pandas · numpy · requests · BeautifulSoup |
| Storage / modeling | SQL · SQLite (star schema) |
| Statistics | scipy · statsmodels (hypothesis tests, CIs, regression) |
| Reporting | Excel (openpyxl/xlsxwriter) · Power BI (DAX) |
| Quality | pytest · ruff · GitHub Actions CI |

## 📂 Repository structure
```
config/      settings.yaml — all scope, sources, and constants
sql/         star-schema DDL + analysis views
src/ncaa_market/
  ingest/    download odds, scrape results & rankings
  clean/     team-name crosswalk, dedupe, join
  features/  ATS, market error, CLV, situational flags
  load/      build the SQLite star schema
  analysis/  cover rates, hypothesis tests, regression, ROI
  report/    mart exports + Excel workbook
notebooks/   one per research-question family
tests/       data-validation + metric-correctness tests
excel/  powerbi/  docs/     the three executive deliverables
```

## 🚀 Quickstart
```bash
# 1. Install (editable, with dev tools)
python -m pip install -e ".[dev]"

# 2. Run the whole pipeline (ingest -> ... -> report)
ncaa-pipeline

# Or run a single stage / list stages
ncaa-pipeline --stage ingest
ncaa-pipeline --list

# 3. Tests
pytest
```

## 📐 Method & metrics
See [`docs/PROJECT_PLAN.md`](docs/PROJECT_PLAN.md) for methodology and
[`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md) for every field and its
sign convention.

## ⚠️ Limitations
Free historical odds skew toward high-major games, so coverage is **not random** —
conference comparisons are interpreted with that selection bias in mind. Full
limitations are documented in the research report.

## 📄 License
MIT — see [`LICENSE`](LICENSE).
