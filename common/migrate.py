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
CREATE TABLE IF NOT EXISTS schema_migrations (
    version String,
    checksum String,
    applied_at DateTime DEFAULT now()
) ENGINE = MergeTree ORDER BY version
"""


def split_statements(sql: str) -> list[str]:
    """Statements separated by `;`, with `--` comment lines removed."""
    lines = [line for line in sql.splitlines() if not line.strip().startswith("--")]
    return [s.strip() for s in "\n".join(lines).split(";") if s.strip()]


def migration_files(schema_dir: Path = SCHEMA_DIR) -> list[Path]:
    files = sorted(p for p in schema_dir.glob("*.sql"))
    bad = [p.name for p in files if not _FILE.match(p.name)]
    if bad:
        raise ValueError(f"migration files must be named NNN_name.sql: {bad}")
    return files


def migrate(client, schema_dir: Path = SCHEMA_DIR) -> list[str]:
    """Apply unapplied files. Returns the names applied in this call."""
    client.command(_BOOKKEEPING)
    applied = dict(client.query("SELECT version, checksum FROM schema_migrations").result_rows)
    done = []
    for path in migration_files(schema_dir):
        sql = path.read_text()
        checksum = hashlib.sha256(sql.encode()).hexdigest()
        if path.name in applied:
            if applied[path.name] != checksum:
                raise RuntimeError(f"{path.name} was edited after it was applied; add a new file instead")
            continue
        for statement in split_statements(sql):
            client.command(statement)
        client.insert("schema_migrations", [[path.name, checksum]], column_names=["version", "checksum"])
        done.append(path.name)
    return done


def main() -> int:
    from common.config import clickhouse_client

    done = migrate(clickhouse_client())
    print("applied: " + ", ".join(done) if done else "nothing to apply; schema is up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
