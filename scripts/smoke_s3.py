"""S3 smoke test: upload a small object, download it, compare SHA-256, clean up."""

import hashlib
import sys
import uuid

from common.config import s3_bucket, s3_client


def main() -> int:
    client, bucket = s3_client(), s3_bucket()
    key = f"smoke/{uuid.uuid4().hex}.txt"
    payload = f"agrocycle smoke test {key}".encode()
    sent = hashlib.sha256(payload).hexdigest()

    client.put_object(Bucket=bucket, Key=key, Body=payload)
    try:
        got = client.get_object(Bucket=bucket, Key=key)["Body"].read()
    finally:
        client.delete_object(Bucket=bucket, Key=key)

    received = hashlib.sha256(got).hexdigest()
    print(f"bucket={bucket} key={key}\nsent    sha256={sent}\nreceived sha256={received}")
    if sent != received:
        print("FAIL: checksum mismatch")
        return 1
    print("OK: S3 round-trip matches")
    return 0


if __name__ == "__main__":
    sys.exit(main())
