"""Read what S3 and the manifests say about each raw pull: object count, bytes and the manifest fields."""
from __future__ import annotations

import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

MANIFEST_SUFFIX = ".manifest.json"
REQUIRED_FIELDS = ("product", "licence", "evidence_type", "retrieval_date")


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
    objects, manifests, data_keys = 0, [], []
    total = 0
    for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(MANIFEST_SUFFIX):
                manifests.append(obj["Key"])
            else:
                objects += 1
                data_keys.append(obj["Key"])
                total += obj["Size"]
    if objects == 0:
        raise ScanError(f"no objects under {prefix}")
    if set(manifests) != {k + MANIFEST_SUFFIX for k in data_keys}:
        missing = sorted({k + MANIFEST_SUFFIX for k in data_keys} - set(manifests))[:3]
        orphans = sorted(set(manifests) - {k + MANIFEST_SUFFIX for k in data_keys})[:3]
        raise ScanError(f"{prefix}: objects and manifests do not pair up (no manifest: {missing}; no object: {orphans})")

    def read(key: str) -> dict:
        try:
            doc = json.loads(client.get_object(Bucket=bucket, Key=key)["Body"].read())
        except ValueError as error:
            raise ScanError(f"{key}: not valid JSON ({error})") from error
        absent = [n for n in REQUIRED_FIELDS if not isinstance(doc.get(n), str) or not doc[n]]
        if absent:
            raise ScanError(f"{key}: manifest lacks {absent}")
        return doc

    with ThreadPoolExecutor(workers) as pool:
        docs = list(pool.map(read, manifests))
    fields, notes = {}, []
    for name in REQUIRED_FIELDS:
        fields[name], note = _most_common([d[name] for d in docs], name)
        if note:
            notes.append(note)
    return {"file_count": objects, "total_bytes": total, "notes": notes, **fields}
