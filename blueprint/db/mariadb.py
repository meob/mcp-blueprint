"""MariaDB adapter.

MariaDB shares the wire protocol and asyncmy driver with MySQL, so this
adapter is a thin subclass that only changes the engine identifier.
"""

from __future__ import annotations

from blueprint.db.mysql import MySQLAdapter


class MariaDBAdapter(MySQLAdapter):
    """Async MariaDB adapter reusing the MySQL asyncmy pool."""

    engine = "mariadb"
