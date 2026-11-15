"""Read what S3 and the manifests say about each raw pull: object count, bytes and the manifest fields."""
from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor

MANIFEST_SUFFIX = ".manifest.json"


class ScanError(RuntimeError):
    pass


def _most_common(values: list[str], what: str) -> tuple[str, str]:
    """(chosen value, a note if the manifests of one pull differ). A tie is refused, not guessed."""
    counts = Counter(values).most_common()
    if len(counts) > 1 and counts[0][1] == counts[1][1]:
        raise ScanError(f"manifests of one pull disagree on {what} with no majority: {[c[0] for c in counts]}")
    note = ""
    if len(counts) > 1:
        note = f"{what} differs between files of this pull: " + "; ".join(f"{v[:60]} ({n})" for v, n in counts)
    return counts[0][0], note


def scan_pull(client, bucket: str, prefix: str, *, workers: int = 16) -> dict:
    """Object count and bytes (manifests excluded) and the manifest fields for everything under `prefix`."""
    objects, manifests = 0, []
    total = 0
    for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(MANIFEST_SUFFIX):
                manifests.append(obj["Key"])
            else:
                objects += 1
                total += obj["Size"]
    if objects == 0:
        raise ScanError(f"no objects under {prefix}")
    if len(manifests) != objects:
        raise ScanError(f"{prefix}: {objects} objects but {len(manifests)} manifests")

    import json

    def read(key: str) -> dict:
        return json.loads(client.get_object(Bucket=bucket, Key=key)["Body"].read())

    with ThreadPoolExecutor(workers) as pool:
        docs = list(pool.map(read, manifests))
    fields, notes = {}, []
    for name in ("product", "licence", "evidence_type", "retrieval_date"):
        fields[name], note = _most_common([d[name] for d in docs], name)
        if note:
            notes.append(note)
    return {"file_count": objects, "total_bytes": total, "notes": notes, **fields}
