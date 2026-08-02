"""Unit tests for pack metadata loading and engine selection."""

from __future__ import annotations

import pytest

from blueprint.errors import ConfigurationError
from blueprint.pack import PackMetadata, load_pack_metadata


def test_load_pack_metadata_reads_engines(tmp_path) -> None:
    (tmp_path / "pack.yaml").write_text(
        "name: pg-dba\nversion: 0.3.0\nengines: [postgresql]\n", encoding="utf-8"
    )
    metadata = load_pack_metadata(tmp_path)
    assert metadata.name == "pg-dba"
    assert metadata.engines == ["postgresql"]
    assert metadata.supports("postgresql")
    assert not metadata.supports("mysql")


def test_missing_manifest_is_engine_agnostic(tmp_path) -> None:
    metadata = load_pack_metadata(tmp_path)
    assert metadata.engines == []
    assert metadata.supports("postgresql")
    assert metadata.supports("mysql")


def test_invalid_engine_in_manifest_raises(tmp_path) -> None:
    (tmp_path / "pack.yaml").write_text("engines: [sqlserver]\n", encoding="utf-8")
    with pytest.raises(ConfigurationError):
        load_pack_metadata(tmp_path)


def test_invalid_manifest_yaml_raises(tmp_path) -> None:
    (tmp_path / "pack.yaml").write_text("engines: [", encoding="utf-8")
    with pytest.raises(ConfigurationError):
        load_pack_metadata(tmp_path)


def test_pack_metadata_supports_any_when_unrestricted() -> None:
    metadata = PackMetadata(name="generic")
    assert metadata.supports("postgresql")
    assert metadata.supports("mysql")
    assert metadata.supports("oracle")
