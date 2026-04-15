"""Configuration — thin re-exports from data-project-manager core."""

from __future__ import annotations

from data_project_manager.config.loader import (
    get_db_path,
    load_config as load_datapm_config,
)

__all__ = ["get_db_path", "load_datapm_config"]
