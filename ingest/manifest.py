"""Manifests: the metadata kept beside every raw file in S3."""

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

# Same labels as the ClickHouse evidence-type enum (specs/tech-stack.md)
EVIDENCE_TYPES = (
    "observed",
    "derived",
    "classified",
    "survey",
    "model_reanalysis",
    "experimental",
    "published",
    "assumption",
)
_SHA256 = re.compile(r"[0-9a-f]{64}")


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class Manifest:
    source_url: str  # where the file came from, or the export route
    product: str
    version: str
    retrieval_date: str  # ISO date, YYYY-MM-DD
    sha256: str
    size_bytes: int
    licence: str
    subset: dict  # what was requested: bbox or point, years or seasons, bands
    evidence_type: str
    scale: str  # for example "30 m raster", "grid", "map unit"
    notes: str = ""  # caveats that must travel with the data

    def __post_init__(self):
        date.fromisoformat(self.retrieval_date)  # ValueError if not a real ISO date
        if self.evidence_type not in EVIDENCE_TYPES:
            raise ValueError(f"evidence_type must be one of {EVIDENCE_TYPES}")
        if not _SHA256.fullmatch(self.sha256):
            raise ValueError("sha256 must be 64 lowercase hex characters")
        if self.size_bytes < 0:
            raise ValueError("size_bytes cannot be negative")
        for name in ("source_url", "product", "version", "licence", "scale"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} is required")

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True) + "\n"

    @classmethod
    def from_json(cls, text: str) -> "Manifest":
        return cls(**json.loads(text))


def build_manifest(path: Path, **fields) -> Manifest:
    """Hash and size the file, then combine them with the descriptive fields."""
    path = Path(path)
    return Manifest(sha256=sha256_file(path), size_bytes=path.stat().st_size, **fields)
