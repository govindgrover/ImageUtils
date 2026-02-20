from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).with_name("config.json")


def _coerce_str_dict(source: dict[str, Any], defaults: dict[str, str]) -> dict[str, str]:
    """Return a shallow dict where known keys are coerced to strings."""
    return {key: str(source.get(key, value)) for key, value in defaults.items()}


def load_app_config(app_key: str, defaults: dict[str, str]) -> dict[str, str]:
    """Load config for a specific app/tool.

    Resolution order:
    1) root-level keys (legacy compatibility)
    2) apps.<app_key> keys (new multi-tool layout)
    3) provided defaults
    """
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
            raw = json.load(config_file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return defaults.copy()

    if not isinstance(raw, dict):
        return defaults.copy()

    merged = defaults.copy()
    merged.update(_coerce_str_dict(raw, defaults))

    apps_section = raw.get("apps")
    if isinstance(apps_section, dict):
        app_section = apps_section.get(app_key)
        if isinstance(app_section, dict):
            merged.update(_coerce_str_dict(app_section, defaults))

    return merged
