"""S3 smoke test: upload a small object, download it and compare SHA-256.

Uses one fixed key under smoke/ that is overwritten on every run, so it needs only
PutObject and GetObject. Deleting is attempted but not required: raw-data users are
not expected to hold s3:DeleteObject.
"""

import hashlib
import sys

from botocore.exceptions import ClientError

from common.config import s3_bucket, s3_client

KEY = "smoke/smoke_test.txt"


def main() -> int:
    client, bucket = s3_client(), s3_bucket()
    payload = b"agrocycle smoke test"
    sent = hashlib.sha256(payload).hexdigest()

    client.put_object(Bucket=bucket, Key=KEY, Body=payload)
    got = client.get_object(Bucket=bucket, Key=KEY)["Body"].read()
    received = hashlib.sha256(got).hexdigest()
    print(f"bucket={bucket} key={KEY}\nsent     sha256={sent}\nreceived sha256={received}")

    try:
        client.delete_object(Bucket=bucket, Key=KEY)
        print("cleaned up the test object")
    except ClientError as err:
        code = err.response["Error"]["Code"]
        print(f"note: could not delete the test object ({code}); it is overwritten on each run")

    if sent != received:
        print("FAIL: checksum mismatch")
        return 1
    print("OK: S3 round-trip matches")
    return 0


if __name__ == "__main__":
    sys.exit(main())
