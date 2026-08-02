"""Loading tool definitions from YAML files."""

from __future__ import annotations

from pathlib import Path

import structlog
import yaml
from pydantic import ValidationError

from blueprint.errors import ToolLoadError
from blueprint.tools.model import ToolMetadata

logger = structlog.get_logger(__name__)


def load_tool_from_file(
    path: str | Path, pack_name: str = "", engine: str | None = None
) -> ToolMetadata | None:
    """Load and validate a single tool definition from a YAML file.

    When ``engine`` is given, tools that do not support it are skipped and
    ``None`` is returned.
    """
    file_path = Path(path)
    try:
        raw = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ToolLoadError(f"cannot read tool file {file_path}: {exc}") from exc
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ToolLoadError(f"invalid YAML in {file_path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ToolLoadError(f"tool file must contain a mapping: {file_path}")

    try:
        metadata = ToolMetadata.model_validate(data)
    except ValidationError as exc:
        raise ToolLoadError(f"invalid tool definition in {file_path}: {exc}") from exc

    metadata.pack_name = pack_name
    metadata.source = str(file_path)
    if engine is not None and not metadata.applies_to(engine):
        logger.debug(
            "skipped_tool_for_engine", tool=metadata.name, engine=engine, source=metadata.source
        )
        return None
    logger.debug("loaded_tool", tool=metadata.name, source=metadata.source, engine=engine)
    return metadata


def load_tools_from_dir(
    tools_dir: str | Path, pack_name: str = "", engine: str | None = None
) -> list[ToolMetadata]:
    """Load all ``*.yaml`` tool definitions found in a directory.

    When ``engine`` is given, tools that do not support it are skipped.
    """
    directory = Path(tools_dir)
    if not directory.is_dir():
        logger.warning("tools_dir_not_found", path=str(directory))
        return []

    tools: list[ToolMetadata] = []
    for file_path in sorted(directory.glob("*.yaml")):
        if file_path.name.startswith("."):
            continue
        tool = load_tool_from_file(file_path, pack_name=pack_name, engine=engine)
        if tool is not None:
            tools.append(tool)
    return tools
