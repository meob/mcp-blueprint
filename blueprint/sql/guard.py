"""SQL safety guard.

Enforces the framework's default policy:

* tools are read-only unless they explicitly declare ``writes: true``;
* parameter values are never interpolated into SQL text (only Jinja2
  control flow and bound placeholders are allowed), so a parameter value
  can never change the statement;
* a single statement per tool, so stacked queries are rejected.

The guard is applied twice: at pack load time on the static template
(fast authoring feedback) and at execution time on the rendered SQL
(non-bypassable).  Classification fails closed: any statement that cannot
be proven read-only is treated as a write.
"""

from __future__ import annotations

import re

from blueprint.errors import ToolSecurityError

_JINJA_BLOCK = re.compile(r"\{%-?.*?-?%\}", re.DOTALL)
_JINJA_INTERPOLATION = re.compile(r"\{\{-?.*?-?\}\}", re.DOTALL)
_LEADING_KEYWORD = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)")
_DOLLAR_QUOTE = re.compile(r"\$[A-Za-z_][A-Za-z0-9_]*\$|\$\$")


def validate_template(sql: str) -> None:
    """Reject templates that interpolate values into SQL text.

    A parameter value must only ever reach the database as a bound
    placeholder (``%(name)s``).  Interpolating it with ``{{ ... }}`` would
    let it change the statement, so it is rejected unconditionally.
    """
    if _JINJA_INTERPOLATION.search(sql):
        raise ToolSecurityError(
            "parameter values must not be interpolated into SQL; use bound "
            "placeholders (%(name)s) and Jinja2 control flow ({% if %}) only"
        )


def split_statements(sql: str) -> list[str]:
    """Split ``sql`` into top-level statements.

    Semicolons inside string literals, quoted identifiers, comments and
    dollar-quoted bodies do not terminate a statement.
    """
    statements: list[str] = []
    buf: list[str] = []
    state = "code"
    dollar_tag: str | None = None
    i, n = 0, len(sql)

    def flush() -> None:
        text = "".join(buf).strip()
        if text:
            statements.append(text)
        buf.clear()

    while i < n:
        char = sql[i]
        nxt = sql[i + 1] if i + 1 < n else ""
        if state == "code":
            if char == "-" and nxt == "-":
                state = "line"
                buf.extend((char, nxt))
                i += 2
            elif char == "#":
                state = "line"
                buf.append(char)
                i += 1
            elif char == "/" and nxt == "*":
                state = "block"
                buf.extend((char, nxt))
                i += 2
            elif char == "'":
                state = "sq"
                buf.append(char)
                i += 1
            elif char == '"':
                state = "dq"
                buf.append(char)
                i += 1
            elif char == "$":
                match = _DOLLAR_QUOTE.match(sql, i)
                if match:
                    dollar_tag = match.group(0)
                    state = "dollar"
                    buf.append(dollar_tag)
                    i += len(dollar_tag)
                else:
                    buf.append(char)
                    i += 1
            elif char == ";":
                flush()
                i += 1
            else:
                buf.append(char)
                i += 1
        elif state == "line":
            if char == "\n":
                state = "code"
            buf.append(char)
            i += 1
        elif state == "block":
            buf.append(char)
            if char == "*" and nxt == "/":
                buf.append(nxt)
                state = "code"
                i += 2
            else:
                i += 1
        elif state == "sq":
            buf.append(char)
            if char == "'":
                if nxt == "'":
                    buf.append(nxt)
                    i += 2
                else:
                    state = "code"
                    i += 1
            else:
                i += 1
        elif state == "dq":
            buf.append(char)
            if char == '"':
                if nxt == '"':
                    buf.append(nxt)
                    i += 2
                else:
                    state = "code"
                    i += 1
            else:
                i += 1
        else:  # dollar quote
            assert dollar_tag is not None
            buf.append(char)
            if sql.startswith(dollar_tag, i):
                buf.append(dollar_tag)
                state = "code"
                i += len(dollar_tag)
            else:
                i += 1

    flush()
    return statements


def leading_keyword(statement: str) -> str:
    """Return the lowercased first keyword of a statement."""
    text = strip_comments(statement).strip().lstrip("(").strip()
    match = _LEADING_KEYWORD.match(text)
    return match.group(1).lower() if match else ""


def statement_kind(statement: str) -> str:
    """Classify a statement as ``read`` or ``write``.

    ``WITH`` is read-only only when it ends in a ``SELECT``.  Anything that
    cannot be proven read-only fails closed to ``write``.
    """
    text = _JINJA_BLOCK.sub(" ", strip_comments(statement))
    text = re.sub(r"\s+", " ", text).strip()
    keyword = leading_keyword(text)
    if keyword == "select":
        return "read"
    if keyword == "with":
        return _with_kind(text)
    return "write"


def _with_kind(text: str) -> str:
    """Classify a ``WITH`` statement by the keyword after its CTE list."""
    index = 0
    length = len(text)

    def skip_ws(pos: int) -> int:
        while pos < length and text[pos].isspace():
            pos += 1
        return pos

    def read_word(pos: int) -> str:
        start = pos
        while pos < length and (text[pos].isalnum() or text[pos] == "_"):
            pos += 1
        return text[start:pos]

    def skip_balanced(pos: int, opener: str) -> int:
        """Skip a balanced parenthesized group starting at ``pos``."""
        depth = 0
        while pos < length:
            char = text[pos]
            if char == opener:
                depth += 1
            elif char in "()":
                depth -= 1
                if depth == 0:
                    return pos + 1
            pos += 1
        return pos

    index = skip_ws(index)
    # Handle WITH RECURSIVE and skip the WITH keyword itself.
    word = read_word(index).lower()
    if word == "recursive":
        index = skip_ws(index + len(word))
        word = read_word(index).lower()
    if word != "with":
        return "write"
    index = skip_ws(index + len(word))

    while index < length:
        # CTE name (possibly followed by a column list).
        name = read_word(index)
        if not name:
            return "write"
        index = skip_ws(index + len(name))
        if index < length and text[index] == "(":
            index = skip_balanced(index, "(")
            index = skip_ws(index)
        if read_word(index).lower() != "as":
            return "write"
        index = skip_ws(index + 2)
        if index >= length or text[index] != "(":
            return "write"
        index = skip_balanced(index, "(")
        index = skip_ws(index)
        if index < length and text[index] == ",":
            index = skip_ws(index + 1)
            continue
        return "read" if read_word(index).lower() == "select" else "write"
    return "write"


def ensure_single_statement(sql: str) -> None:
    """Reject SQL containing more than one top-level statement."""
    statements = split_statements(sql)
    if len(statements) != 1:
        raise ToolSecurityError(f"SQL must contain exactly one statement, found {len(statements)}")


def ensure_read_only(sql: str) -> None:
    """Reject SQL that is not a single read-only statement."""
    ensure_single_statement(sql)
    statements = split_statements(sql)
    if statement_kind(statements[0]) != "read":
        kind = leading_keyword(statements[0]) or "empty"
        raise ToolSecurityError(
            f"statement is not read-only (leading keyword: '{kind}'); "
            "declare 'writes: true' to allow non-SELECT statements"
        )


def strip_comments(sql: str) -> str:
    """Remove SQL line and block comments while keeping string literals."""
    out: list[str] = []
    state = "code"
    i, n = 0, len(sql)
    while i < n:
        char = sql[i]
        nxt = sql[i + 1] if i + 1 < n else ""
        if state == "code":
            if char == "-" and nxt == "-":
                state = "line"
                i += 2
            elif char == "#":
                state = "line"
                i += 1
            elif char == "/" and nxt == "*":
                state = "block"
                i += 2
            elif char == "'":
                out.append(char)
                state = "sq"
                i += 1
            else:
                out.append(char)
                i += 1
        elif state == "line":
            if char == "\n":
                state = "code"
                out.append("\n")
            i += 1
        elif state == "block":
            if char == "*" and nxt == "/":
                state = "code"
                i += 2
            else:
                i += 1
        else:  # single-quoted string
            out.append(char)
            if char == "'":
                if nxt == "'":
                    out.append(nxt)
                    i += 2
                else:
                    state = "code"
                    i += 1
            else:
                i += 1
    return "".join(out)
