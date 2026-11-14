"""Skip the tests that need the raw Marsden files when those files are not on this machine.

Raw data is not in git and most of the team has no S3 access, so on a fresh clone these tests
cannot run. They skip with a reason instead of failing. The tests that do not read the raw files
(equal-area weighting by hand, the phase-label check, the lineage rows) always run.
"""

import pytest

from transform.marsden import marsden_repro as m

NEEDS_RAW_FIXTURES = {"result", "summary", "raw_frames"}
NEEDS_RAW_TESTS = {
    "test_raw_files_match_manifest",
    "test_tampered_input_is_detected",
    "test_rerun_gives_identical_tables",
}
REQUIRED = (*m.INPUT_FILES, "MANIFEST.json")


def raw_available() -> bool:
    return all((m.DEFAULT_RAW / name).exists() for name in REQUIRED)


def pytest_collection_modifyitems(config, items):
    if raw_available():
        return
    skip = pytest.mark.skip(
        reason=f"Marsden raw files not found in {m.DEFAULT_RAW} "
        "(raw data is not in git; ask the data engineer for the five files and MANIFEST.json)"
    )
    for item in items:
        if not str(item.fspath).startswith(str(__file__).rsplit("/", 1)[0]):
            continue
        needs_raw = NEEDS_RAW_FIXTURES & set(item.fixturenames) or item.originalname in NEEDS_RAW_TESTS
        if needs_raw:
            item.add_marker(skip)
