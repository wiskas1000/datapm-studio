"""Read datapm configuration from ~/.datapm/config.json."""

import json
from pathlib import Path


def get_datapm_dir() -> Path:
    """Return the datapm config directory."""
    return Path.home() / ".datapm"


def get_db_path() -> Path:
    """Return the path to the datapm SQLite database."""
    return get_datapm_dir() / "projects.db"


def load_datapm_config() -> dict:
    """Load and return the datapm config.json as a dict.

    Returns an empty dict if the config file doesn't exist yet.
    """
    config_path = get_datapm_dir() / "config.json"
    if config_path.exists():
        return json.loads(config_path.read_text())
    return {}
