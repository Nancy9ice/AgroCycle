"""Apply the numbered SQL files in schema/ to ClickHouse, once each, in order.

    uv run python -m common.migrate

Safe to rerun: applied files are recorded in `schema_migrations` with their checksum. An applied file
that was edited afterwards is an error (add a new numbered file instead).
"""

import hashlib
import re
import sys
from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schema"
_FILE = re.compile(r"^\d{3}_[a-z0-9_]+\.sql$")

_BOOKKEEPING = """
CREATE TABLE IF NOT EXISTS {name} (
    version String,
    checksum String,
    applied_at DateTime DEFAULT now()
) ENGINE = MergeTree ORDER BY version
"""


def split_statements(sql: str) -> list[str]:
    """Statements separated by `;`. `--` comments (whole-line or trailing) are dropped, and a `;`
    inside a single-quoted string does not split. Write statements so they can be rerun (IF NOT
    EXISTS): a file that fails part-way is not recorded, and is applied again from its first statement."""
    statements, current, quoted, i = [], [], False, 0
    while i < len(sql):
        char = sql[i]
        if char == "'":
            quoted = not quoted
        elif not quoted and sql.startswith("--", i):
            i = sql.find("\n", i) if "\n" in sql[i:] else len(sql)
            continue
        elif not quoted and char == ";":
            statements.append("".join(current).strip())
            current = []
            i += 1
            continue
        current.append(char)
        i += 1
    statements.append("".join(current).strip())
    return [s for s in statements if s]


def with_prefix(statement: str, prefix: str) -> str:
    """Name the tables a statement creates `<prefix><name>`. The live tests use this to work in
    scratch tables beside the real ones; the real run uses an empty prefix."""
    if not prefix:
        return statement
    if not re.match(r"\s*CREATE TABLE IF NOT EXISTS \w+", statement):
        # anything else (ALTER, a view, a table without IF NOT EXISTS) would reach the real tables
        raise ValueError(f"a prefix works only with CREATE TABLE IF NOT EXISTS, got: {statement[:60]!r}")
    return re.sub(r"(CREATE TABLE IF NOT EXISTS )(\w+)", rf"\g<1>{prefix}\g<2>", statement)


def migration_files(schema_dir: Path = SCHEMA_DIR) -> list[Path]:
    files = sorted(p for p in schema_dir.glob("*.sql"))
    bad = [p.name for p in files if not _FILE.match(p.name)]
    if bad:
        raise ValueError(f"migration files must be named NNN_name.sql: {bad}")
    return files


def migrate(client, schema_dir: Path = SCHEMA_DIR, prefix: str = "") -> list[str]:
    """Apply unapplied files. Returns the names applied in this call."""
    book = f"{prefix}schema_migrations"
    client.command(_BOOKKEEPING.format(name=book))
    applied = dict(client.query(f"SELECT version, checksum FROM {book}").result_rows)
    done = []
    for path in migration_files(schema_dir):
        sql = path.read_text()
        checksum = hashlib.sha256(sql.encode()).hexdigest()
        if path.name in applied:
            if applied[path.name] != checksum:
                raise RuntimeError(f"{path.name} was edited after it was applied; add a new file instead")
            continue
        for statement in split_statements(sql):
            client.command(with_prefix(statement, prefix))
        client.insert(book, [[path.name, checksum]], column_names=["version", "checksum"])
        done.append(path.name)
    return done


def main() -> int:
    from common.config import clickhouse_client

    done = migrate(clickhouse_client())
    print("applied: " + ", ".join(done) if done else "nothing to apply; schema is up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
