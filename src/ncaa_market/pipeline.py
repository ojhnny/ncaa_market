"""End-to-end pipeline orchestrator.

Runs the six stages in order. Each stage is implemented in its own sub-package
and filled in over the course of the project; until then a stage logs a TODO so
the command runs without crashing and the overall shape stays visible.

Run everything:        ncaa-pipeline
Run one stage:         ncaa-pipeline --stage ingest
List stages:           ncaa-pipeline --list
"""

from __future__ import annotations

import argparse
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s")
log = logging.getLogger("ncaa_market")

# Ordered stage registry: name -> human description. Implementations are wired in
# per phase; calling an unimplemented stage logs a TODO rather than failing.
STAGES: list[tuple[str, str]] = [
    ("ingest", "Download/scrape raw odds, results, rankings -> data/raw/"),
    ("clean", "Clean, dedupe, crosswalk team names, join -> data/staging/"),
    ("features", "Compute ATS, market error, CLV, situational flags"),
    ("load", "Build SQLite star schema -> data/marts/ncaa_market.sqlite"),
    ("analysis", "Cover rates, hypothesis tests, regression, ROI backtests"),
    ("report", "Export marts + build Excel/Power BI feeds"),
]


def _run_stage(name: str) -> None:
    log.info("STAGE '%s' — not yet implemented (TODO).", name)


def run_all() -> None:
    for name, desc in STAGES:
        log.info("=== %s : %s ===", name, desc)
        _run_stage(name)


def main() -> None:
    parser = argparse.ArgumentParser(description="NCAA market-efficiency pipeline.")
    parser.add_argument("--stage", choices=[s for s, _ in STAGES], help="Run a single stage.")
    parser.add_argument("--list", action="store_true", help="List stages and exit.")
    args = parser.parse_args()

    if args.list:
        for name, desc in STAGES:
            print(f"  {name:10s} {desc}")
        return

    if args.stage:
        _run_stage(args.stage)
    else:
        run_all()


if __name__ == "__main__":
    main()
