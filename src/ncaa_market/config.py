"""Central configuration access.

Loads ``config/settings.yaml`` exactly once and exposes it as a plain dict,
plus a couple of conveniences (repo-root discovery and absolute-path resolution)
so that no other module ever hard-codes a path or re-reads the file.

Usage
-----
>>> from ncaa_market.config import get_config, resolve_path
>>> cfg = get_config()
>>> cfg["seasons"]["start"]
2008
>>> resolve_path(cfg["paths"]["database"])   # -> absolute Path under repo root
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


def project_root() -> Path:
    """Return the repository root.

    This file lives at ``<root>/src/ncaa_market/config.py``, so the root is
    three parents up. Resolving it this way means the package works no matter
    what the current working directory is.
    """
    return Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def get_config() -> dict[str, Any]:
    """Load and cache ``config/settings.yaml`` as a dict."""
    cfg_path = project_root() / "config" / "settings.yaml"
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config file not found: {cfg_path}")
    with cfg_path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def resolve_path(relative: str | Path) -> Path:
    """Resolve a repo-relative path (as stored in settings.yaml) to an absolute Path.

    Absolute inputs are returned unchanged.
    """
    p = Path(relative)
    return p if p.is_absolute() else (project_root() / p)


def seasons_range() -> range:
    """Inclusive range of season-ids configured for the study."""
    cfg = get_config()
    return range(cfg["seasons"]["start"], cfg["seasons"]["end"] + 1)
