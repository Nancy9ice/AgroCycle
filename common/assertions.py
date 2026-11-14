"""Post-load assertions. Each returns a list of problems; an empty list means the check passed.

They run on the staging table before the swap, so a failure leaves the live table untouched.
Table and column names come from the TABLES registry, never from user input.
"""

from common.schemas import TABLES


def _scalar(client, sql: str) -> int:
    return int(client.query(sql).result_rows[0][0])


def check_table(client, table: str, expected_rows: int, target: str | None = None) -> list[str]:
    """Row count matches the frame, no empty key text, no duplicate natural key.

    `table` picks the registry entry; `target` is the table actually queried (the staging copy).
    """
    spec = TABLES[table]
    table = target or table
    problems = []
    rows = _scalar(client, f"SELECT count() FROM `{table}`")
    if rows != expected_rows:
        problems.append(f"{table}: expected {expected_rows} rows, found {rows}")
    for column in spec.text_keys:
        empty = _scalar(client, f"SELECT count() FROM `{table}` WHERE `{column}` = ''")
        if empty:
            problems.append(f"{table}: {empty} rows with an empty {column}")
    keys = ", ".join(f"`{c}`" for c in spec.key)
    duplicates = _scalar(client, f"SELECT count() - uniqExact({keys}) FROM `{table}`")
    if duplicates:
        problems.append(f"{table}: {duplicates} duplicate rows on key ({', '.join(spec.key)})")
    return problems


def orphan_indicators(client, table: str, column: str = "indicator_id") -> list[str]:
    """Indicator ids in `table` with no row in indicator_lineage (tech-stack: every indicator is linked)."""
    sql = (
        f"SELECT DISTINCT `{column}` FROM `{table}` "
        f"WHERE `{column}` NOT IN (SELECT indicator_id FROM indicator_lineage) ORDER BY 1"
    )
    return [f"{table}: indicator {row[0]!r} has no indicator_lineage row" for row in client.query(sql).result_rows]


def table_hash(client, table: str) -> int:
    """Order-independent content hash, ignoring load_id, so two loads of one frame compare equal."""
    return _scalar(client, f"SELECT sum(cityHash64(* EXCEPT (load_id))) FROM `{table}`")
