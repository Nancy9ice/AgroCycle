"""ClickHouse smoke test: SELECT 1, then create, query and drop a scratch table."""

import sys
import uuid

from common.config import clickhouse_client


def main() -> int:
    client = clickhouse_client()
    if client.query("SELECT 1").result_rows != [(1,)]:
        print("FAIL: SELECT 1")
        return 1
    database = client.query("SELECT currentDatabase()").result_rows[0][0]
    print(f"connected, server version {client.server_version}, database {database}")
    if database != "agrocycle":
        print("FAIL: expected database 'agrocycle'")
        return 1

    table = f"smoke_{uuid.uuid4().hex[:8]}"
    client.command(f"CREATE TABLE {table} (id UInt32, note String) ENGINE = MergeTree ORDER BY id")
    try:
        client.insert(table, [[1, "a"], [2, "b"]], column_names=["id", "note"])
        count = client.query(f"SELECT count() FROM {table}").result_rows[0][0]
    finally:
        client.command(f"DROP TABLE IF EXISTS {table}")

    if count != 2:
        print(f"FAIL: expected 2 rows, got {count}")
        return 1
    print("OK: ClickHouse create, insert, query and drop work")
    return 0


if __name__ == "__main__":
    sys.exit(main())
