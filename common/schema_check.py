"""Offline check: the SQL files and the Pandera schemas describe the same columns.

    uv run python -m common.schema_check

Needs no database, so `make check` runs it for everyone. Compares column names and the evidence-type
Enum for every table in common.schemas.TABLES.
"""

import re
import sys

from common.migrate import SCHEMA_DIR, migration_files, split_statements
from common.schemas import TABLES
from ingest.manifest import EVIDENCE_TYPES

_CREATE = re.compile(r"CREATE TABLE IF NOT EXISTS (\w+) \((.*)\)\s*ENGINE", re.DOTALL)
_ENUM_COLUMN = re.compile(r"(\w+)\s+Enum8\(([^)]*)\)")


def sql_tables(schema_dir=SCHEMA_DIR) -> dict[str, str]:
    """Table name -> the text between the column parentheses, across all migration files."""
    tables = {}
    for path in migration_files(schema_dir):
        for statement in split_statements(path.read_text()):
            match = _CREATE.search(statement)
            if match:
                tables[match.group(1)] = match.group(2)
    return tables


def columns(body: str) -> list[str]:
    """Column names, in order. Splits on commas outside parentheses (Enum8 and LowCardinality)."""
    parts, depth, current = [], 0, ""
    for char in body:
        depth += char == "("
        depth -= char == ")"
        if char == "," and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += char
    parts.append(current)
    return [p.split()[0] for p in parts if p.strip()]


def _allowed_values(schema, column: str) -> set | None:
    """The values a column's `isin` check allows, or None if it has no such check."""
    if column not in schema.columns:
        return None
    for check in schema.columns[column].checks:
        if check.name == "isin":
            return set(check.statistics["allowed_values"])
    return None


def problems(schema_dir=SCHEMA_DIR) -> list[str]:
    found = []
    tables = sql_tables(schema_dir)
    for name, spec in TABLES.items():
        if name not in tables:
            found.append(f"{name}: no CREATE TABLE in schema/")
            continue
        sql_cols = columns(tables[name])
        expected = [*spec.schema.columns, "load_id"]
        if sql_cols != expected:
            found.append(f"{name}: SQL columns {sql_cols} differ from schema columns {expected}")
        for column, labels in _ENUM_COLUMN.findall(tables[name]):
            names = set(re.findall(r"'([^']+)'\s*=", labels))
            allowed = _allowed_values(spec.schema, column)
            if column == "evidence_type":
                allowed = set(EVIDENCE_TYPES)  # one list for the whole project (ingest.manifest)
            if allowed is not None and names != allowed:
                found.append(f"{name}.{column}: SQL Enum {sorted(names)} differs from the schema's {sorted(allowed)}")
        if spec.partition_column and spec.partition_column not in sql_cols:
            found.append(f"{name}: partition column {spec.partition_column} is not a column")
    return found


def main() -> int:
    found = problems()
    for line in found:
        print(f"FAIL: {line}")
    if not found:
        print(f"OK: {len(TABLES)} tables, SQL and Pandera schemas agree")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
