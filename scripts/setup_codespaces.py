"""Setup script for Codespaces - install deps and test ClickHouse connection."""
import subprocess
import sys

print("=" * 60)
print("AgroCycle Phase 5 - Codespaces Setup")
print("=" * 60)

# Step 1: Install dependencies
print("\n1. Installing dependencies...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "clickhouse-connect", "boto3", "pandas", "numpy"])

# Step 2: Test ClickHouse connection
print("\n2. Testing ClickHouse connection...")
import clickhouse_connect

host = '13.140.182.249'
configs = [
    ("Port 9000 (native TCP)", {"port": 9000, "secure": False}),
    ("Port 8123 (HTTP)", {"port": 8123, "secure": False}),
]

for label, kwargs in configs:
    print(f"   Trying {label}...", end=" ")
    try:
        c = clickhouse_connect.get_client(
            host=host,
            username='hannah_igboke',
            password='TLX0NWZnJU7AKGpo',
            database='agrocycle',
            connect_timeout=10,
            **kwargs
        )
        r = c.query('SELECT count() FROM hls_valid_pixels')
        print("SUCCESS!")
        print(f"   hls_valid_pixels: {r.result_rows[0][0]} rows")
        tables = c.query("SHOW TABLES")
        print(f"   Tables: {[row[0] for row in tables.result_rows]}")
        sys.exit(0)
    except Exception as e:
        print(f"FAILED: {str(e)[:60]}")

print("\n   Could not connect. Check .env file and ClickHouse server status.")
print("\n3. To run Phase 5: python -m transform.hls.phase5 --sample 1")
print("   Full run: python -m transform.hls.phase5 --load")