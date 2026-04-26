"""Runtime YAML configuration loader with file-mtime hot-reload caching.

Single access point for all YAML configuration files. Cache is invalidated
automatically when files change on disk — no restart needed.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# Resolve backend/ directory from this file's location: backend/app/core/config_loader.py
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class RuntimeConfigLoader:
    """Load and cache YAML configuration files with hot-reload support.

    All methods are synchronous — YAML loading is fast and does not need async.
    Cache is class-level (shared across all instances / requests).
    """

    # key -> (data, load_timestamp, file_mtime)
    _cache: dict[str, tuple[dict[str, Any], float, float]] = {}

    # Seconds between mtime checks — avoids stat() on every request
    _mtime_check_interval: float = 5.0

    # Last time we checked mtime for each key
    _last_mtime_check: dict[str, float] = {}

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    @classmethod
    def _resolve_path(cls, relative_path: str) -> Path:
        return _BACKEND_DIR / "config" / relative_path

    @classmethod
    def _load_yaml_file(cls, path: Path) -> dict[str, Any]:
        if not path.exists():
            logger.warning(f"Config file not found: {path}")
            return {}
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        logger.debug(f"Loaded config: {path}")
        return data or {}

    @classmethod
    def _get_mtime(cls, path: Path) -> float:
        try:
            return path.stat().st_mtime
        except OSError:
            return 0.0

    @classmethod
    def _should_reload(cls, cache_key: str, path: Path) -> bool:
        if cache_key not in cls._cache:
            return True
        now = time.monotonic()
        last_check = cls._last_mtime_check.get(cache_key, 0.0)
        if now - last_check < cls._mtime_check_interval:
            return False
        cls._last_mtime_check[cache_key] = now
        current_mtime = cls._get_mtime(path)
        _, _, cached_mtime = cls._cache[cache_key]
        return current_mtime != cached_mtime

    @classmethod
    def _load_with_cache(cls, cache_key: str, path: Path) -> dict[str, Any]:
        if cls._should_reload(cache_key, path):
            data = cls._load_yaml_file(path)
            mtime = cls._get_mtime(path)
            cls._cache[cache_key] = (data, time.monotonic(), mtime)
            cls._last_mtime_check[cache_key] = time.monotonic()
        return cls._cache[cache_key][0]

    # -------------------------------------------------------------------------
    # Public API — page configs
    # -------------------------------------------------------------------------

    @classmethod
    def load_page_config(cls, page_type: str) -> dict[str, Any]:
        """Load config/pages/{page_type}.yaml"""
        path = cls._resolve_path(f"pages/{page_type}.yaml")
        return cls._load_with_cache(f"pages/{page_type}", path)

    @classmethod
    def get_attribute_config(cls, page_type: str, field_name: str) -> dict[str, Any] | None:
        """Find a single attribute by name within a page config."""
        config = cls.load_page_config(page_type)
        return next(
            (a for a in config.get("attributes", []) if a.get("name") == field_name),
            None,
        )

    # -------------------------------------------------------------------------
    # Public API — product definition configs
    # -------------------------------------------------------------------------

    @classmethod
    def load_product_definition_config(cls, scope: str) -> dict[str, Any]:
        """Load config/product_definition/{scope}.yaml"""
        path = cls._resolve_path(f"product_definition/{scope}.yaml")
        return cls._load_with_cache(f"product_definition/{scope}", path)

    @classmethod
    def get_entity_types(cls, scope: str) -> list[str]:
        """Return valid entity types for a scope.

        Reads the top-level ``entity_types`` list if present, otherwise
        falls back to the keys of the ``entities`` dict.
        """
        config = cls.load_product_definition_config(scope)
        if "entity_types" in config:
            return list(config["entity_types"])
        entities = config.get("entities", {})
        return list(entities.keys())

    @classmethod
    def get_glazing_types(cls) -> list[str]:
        """Return valid glazing unit types from the glazing product definition config."""
        config = cls.load_product_definition_config("glazing")
        return list(config.get("glazing_types", []))

    # -------------------------------------------------------------------------
    # Public API — generic configs
    # -------------------------------------------------------------------------

    @classmethod
    def load_config(cls, config_name: str) -> dict[str, Any]:
        """Load config/{config_name}.yaml (ui_components, glazing_defaults, etc.)"""
        path = cls._resolve_path(f"{config_name}.yaml")
        return cls._load_with_cache(config_name, path)

    @classmethod
    def get_ui_component_aliases(cls) -> dict[str, str]:
        """Return ui_component alias map from ui_components.yaml."""
        return cls.load_config("ui_components").get("aliases", {})

    @classmethod
    def get_ui_component_fallbacks(cls) -> dict[str, str]:
        """Return data_type → default component map from ui_components.yaml."""
        return cls.load_config("ui_components").get("fallbacks_by_data_type", {})

    @classmethod
    def get_relations_fields(cls, page_type: str) -> list[str]:
        """Return field names that load options from the relations system."""
        relations = cls.load_config("ui_components").get("relations_fields", {})
        return relations.get(page_type, [])

    # -------------------------------------------------------------------------
    # Public API — page type discovery
    # -------------------------------------------------------------------------

    @classmethod
    def get_page_types(cls) -> list[str]:
        """Return all available page types by scanning config/pages/*.yaml."""
        pages_dir = cls._resolve_path("pages")
        if not pages_dir.exists():
            return ["profile", "accessories", "glazing"]
        return [p.stem for p in sorted(pages_dir.glob("*.yaml"))]

    # -------------------------------------------------------------------------
    # Cache control
    # -------------------------------------------------------------------------

    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cached configs. Use in tests or after bulk YAML edits."""
        cls._cache.clear()
        cls._last_mtime_check.clear()

    @classmethod
    def disable_mtime_check(cls) -> None:
        """Always reload on next access. Use in tests."""
        cls._mtime_check_interval = 0.0

    @classmethod
    def enable_mtime_check(cls) -> None:
        """Restore normal 5-second mtime check interval."""
        cls._mtime_check_interval = 5.0
