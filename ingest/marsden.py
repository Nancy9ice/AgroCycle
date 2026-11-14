"""Marsden Farm raw data: the Davis et al. (2012) supplement, in two sets.

1. DS2's original files, kept under DS2's retrieval date so DS2's code and checksums apply
   unchanged: the paper PDF, Tables S1, S3 and S4 and Text S1, plus DS2's checksum list as
   `MANIFEST.json`. Every file must match the SHA-256 in DS2's tracked manifest.
2. The Europe PMC supplementary-files ZIP, exactly as received. It holds all seven supplement
   files and the figures, and is an independent copy of the same source.
"""

import hashlib
import json
import zipfile
from datetime import date
from pathlib import Path, PurePosixPath

from ingest.checks import CheckResult, check_opens
from ingest.items import Item
from ingest.manifest import Manifest, build_manifest
from ingest.subset import check_budget, subset_record

SOURCE = "marsden"
BUDGET_BYTES = 50_000_000
DS2_VERSION = "pone.0047149-supplement"
DS2_FILES = (
    "pone.0047149.pdf",
    "pone.0047149.s002.docx",
    "pone.0047149.s004.docx",
    "pone.0047149.s005.docx",
    "pone.0047149.s007.docx",
)
DS2_MANIFEST = Path(__file__).resolve().parent.parent / "transform/marsden/manifests/2026-11-13.json"
ZIP_VERSION = "europepmc-supplementary-zip"
ZIP_NAME = "PMC3468434_SupplementaryFiles.zip"
ZIP_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC3468434/supplementaryFiles"
SCALE = "single research site (Marsden Farm, Boone County, Iowa)"
LICENCE = (
    "Creative Commons Public Domain declaration, as stated on the article's PMC page "
    "(https://pmc.ncbi.nlm.nih.gov/articles/PMC3468434/). DS2's manifest said CC BY and "
    "asked to confirm; the page states the public domain declaration."
)


def default_dir() -> Path:
    return Path.home() / "agrocycle_marsden"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _missing(name: str, reason: str) -> Item:
    placeholder = Manifest(
        source_url="n/a", product="n/a", version=DS2_VERSION, retrieval_date="2026-11-13",
        sha256="0" * 64, size_bytes=0, licence="n/a", subset={}, evidence_type="assumption",
        scale="n/a", notes=reason,
    )
    return Item(Path(name), placeholder, CheckResult([f"{name}: {reason}"]), SOURCE)


def _ds2_items(raw: Path, ds2: dict[str, dict]) -> list[Item]:
    items = []
    for name in DS2_FILES:
        entry, path = ds2[name], raw / name
        if not path.exists():
            items.append(_missing(name, "file not found in the Marsden folder"))
            continue
        checks = check_opens(path)
        if _sha256(path.read_bytes()) != entry["sha256"]:
            checks.problems.append(f"{name}: differs from the SHA-256 in DS2's manifest")
        evidence = "published" if name.endswith(".pdf") else "experimental"
        manifest = build_manifest(
            path,
            source_url=entry["source_url"],
            product=entry["product"],
            version=DS2_VERSION,
            retrieval_date=entry["retrieval_date"],
            licence=LICENCE,
            subset=subset_record("document", doi=entry["doi"], description=entry["description"]),
            evidence_type=evidence,
            scale=SCALE,
            notes=(
                f"DS2's original file. DS2's note: {entry['retrieval_note']}. "
                "Matches the SHA-256 in transform/marsden/manifests/2026-11-13.json."
            ),
        )
        items.append(Item(path, manifest, checks, SOURCE))
    checklist = build_manifest(
        DS2_MANIFEST,
        source_url="https://github.com/Nancy9ice/AgroCycle (transform/marsden/manifests/2026-11-13.json)",
        product="DS2 checksum list for the Marsden raw files",
        version=DS2_VERSION,
        retrieval_date="2026-11-13",
        licence="Project file (same terms as the repository)",
        subset=subset_record("checksum-list", files=list(ds2)),
        evidence_type="derived",
        scale="n/a",
        notes="DS2's MANIFEST.json, which marsden_repro.py reads from the raw folder.",
    )
    items.append(Item(DS2_MANIFEST, checklist, check_opens(DS2_MANIFEST), SOURCE, "MANIFEST.json"))
    return items


def _zip_item(path: Path, ds2: dict[str, dict]) -> Item:
    if not path.exists():
        return _missing(path.name, "Europe PMC ZIP not found")
    members, same = {}, []
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            name = PurePosixPath(info.filename).name  # read in memory; nothing is extracted
            members[name] = _sha256(archive.read(info))
            if name in ds2 and members[name] == ds2[name]["sha256"]:
                same.append(name)
    retrieved = date.fromtimestamp(path.stat().st_mtime).isoformat()
    manifest = build_manifest(
        path,
        source_url=ZIP_URL,
        product="Davis et al. 2012 PLOS ONE supporting information (Europe PMC copy)",
        version=ZIP_VERSION,
        retrieval_date=retrieved,
        licence=LICENCE,
        subset=subset_record("zip", pmcid="PMC3468434", member_sha256=members),
        evidence_type="experimental",
        scale=SCALE,
        notes=(
            f"The ZIP exactly as Europe PMC returned it ({len(members)} files: the seven "
            "supplement files and the figures; no PDF). Byte-identical to DS2's originals: "
            + ", ".join(sorted(same)) + "."
        ),
    )
    return Item(path, manifest, check_opens(path), SOURCE)


def plan(base: Path | None = None) -> list[Item]:
    """Items for DS2's originals (in `base`) and the Europe PMC ZIP (in `base/europepmc`)."""
    base = Path(base) if base else default_dir()
    ds2 = {e["file"]: e for e in json.loads(DS2_MANIFEST.read_text())}
    items = _ds2_items(base, ds2) + [_zip_item(base / "europepmc" / ZIP_NAME, ds2)]
    check_budget(SOURCE, sum(i.manifest.size_bytes for i in items), BUDGET_BYTES)
    return items
