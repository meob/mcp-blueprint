"""Jinja2 rendering of SQL templates.

Templates may use conditional blocks to build optional filters:

.. code-block:: sql

   SELECT * FROM pg_stat_activity
   {% if database %}
   WHERE datname = %(database)s
   {% endif %}

Parameter placeholders use psycopg3 named style (``%(name)s``) and survive
Jinja2 rendering untouched.
"""

from __future__ import annotations

from typing import Any

from jinja2 import Environment, StrictUndefined, TemplateError, UndefinedError

from blueprint.errors import SQLRenderError


class SQLRenderer:
    """Renders SQL templates against validated tool parameters."""

    def __init__(self) -> None:
        self._env = Environment(undefined=StrictUndefined, keep_trailing_newline=True)

    def render(self, template: str, params: dict[str, Any]) -> str:
        """Render ``template`` using ``params`` and return the resulting SQL."""
        try:
            return self._env.from_string(template).render(**params)
        except (UndefinedError, TemplateError) as exc:
            raise SQLRenderError(f"failed to render SQL template: {exc}") from exc
