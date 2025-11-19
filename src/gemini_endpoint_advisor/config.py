"""Configuration loading for Gemini Endpoint Advisor."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import yaml


DEFAULT_CONFIG: Dict[str, Any] = {
    "min_macos_version": "14.0",
    "max_versions_behind": 2,
    "require_filevault": True,
    "require_firewall": True,
    "max_noncompliant_percentage": 10,
    "slack": {
        "title": "Weekly Endpoint Posture Summary",
        "channel": "#client-platform",
        "include_emojis": True,
    },
}


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """Load YAML config from disk or return defaults.

    Resolution order:
    1. Explicit `path` argument (if provided)
    2. GEMINI_ENDPOINT_ADVISOR_CONFIG environment variable
    3. Built-in DEFAULT_CONFIG
    """
    config_path = path or os.environ.get("GEMINI_ENDPOINT_ADVISOR_CONFIG")
    if not config_path:
        return DEFAULT_CONFIG.copy()

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    merged: Dict[str, Any] = DEFAULT_CONFIG.copy()
    for key, value in data.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key].update(value)  # shallow merge
        else:
            merged[key] = value

    return merged
