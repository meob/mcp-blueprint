"""Pack metadata loaded from ``pack.yaml``.

The pack manifest is optional: when absent, a pack is considered engine-agnostic
and loads on every configured engine.  When present, the ``engines`` field
declares which database engines the pack targets; the application skips packs
that do not match the configured engine.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator

from blueprint.engines import SUPPORTED_ENGINES
from blueprint.errors import ConfigurationError


class PackMetadata(BaseModel):
    """Manifest of a single pack."""

    name: str = ""
    version: str = ""
    description: str = ""
    instructions: str = ""
    engines: list[str] = Field(default_factory=list)

    @field_validator("engines")
    @classmethod
    def _validate_engines(cls, value: list[str]) -> list[str]:
        seen: set[str] = set()
        for engine in value:
            if not engine or engine in seen:
                raise ValueError(f"duplicate or empty engine: {engine!r}")
            if engine not in SUPPORTED_ENGINES:
                raise ValueError(f"unsupported engine: {engine}")
            seen.add(engine)
        return value

    def supports(self, engine: str) -> bool:
        """Whether the pack declares ``engine`` (any engine when not declared)."""
        return not self.engines or engine in self.engines


def load_pack_metadata(pack_dir: str | Path) -> PackMetadata:
    """Read the pack manifest, tolerating a missing ``pack.yaml``."""
    manifest = Path(pack_dir) / "pack.yaml"
    if not manifest.is_file():
        return PackMetadata(name=Path(pack_dir).name)
    try:
        data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigurationError(f"invalid pack manifest {manifest}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigurationError(f"pack manifest must be a mapping: {manifest}")
    try:
        return PackMetadata.model_validate(data)
    except ValidationError as exc:
        raise ConfigurationError(f"invalid pack manifest {manifest}: {exc}") from exc
