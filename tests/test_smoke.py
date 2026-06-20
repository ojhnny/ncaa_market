"""Smoke tests — verify the package imports and config loads.

These run in CI on every push so a broken import or malformed settings.yaml is
caught immediately. Real data-validation and metric-correctness tests are added
in later phases.
"""

from __future__ import annotations

import ncaa_market
from ncaa_market.config import get_config, project_root, resolve_path


def test_package_has_version() -> None:
    assert isinstance(ncaa_market.__version__, str)


def test_config_loads_core_keys() -> None:
    cfg = get_config()
    assert cfg["seasons"]["start"] == 2008
    assert cfg["seasons"]["end"] == 2024
    # The break-even threshold must be the -110 vig value, not 0.50.
    assert abs(cfg["vig"]["breakeven_cover_rate"] - 0.5238) < 1e-6


def test_resolve_path_is_absolute() -> None:
    p = resolve_path(get_config()["paths"]["database"])
    assert p.is_absolute()
    assert p.is_relative_to(project_root())
