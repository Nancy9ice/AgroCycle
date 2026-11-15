import clickhouse_connect
c = clickhouse_connect.get_client(
    host="13.140.182.249", port=8123, username="hannah_igboke",
    password="TLX0NWZnJU7AKGpo", database="agrocycle", secure=False,
)
print(c.query("SELECT count() FROM hls_valid_pixels").result_rows)