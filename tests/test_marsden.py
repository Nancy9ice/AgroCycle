import zipfile

import pytest

from ingest import marsden


def _docx(path, text="x"):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", text)


def _problems(items):
    return [p for i in items for p in i.checks.problems]


def test_missing_files_are_reported_and_nothing_is_ready(tmp_path):
    items = marsden.plan(tmp_path)
    text = " ".join(_problems(items))
    for name in marsden.DS2_FILES:
        assert f"{name}: file not found" in text
    assert "Europe PMC ZIP not found" in text


def test_a_file_that_differs_from_ds2_manifest_is_rejected(tmp_path):
    _docx(tmp_path / "pone.0047149.s002.docx", "not the original")
    items = marsden.plan(tmp_path)
    assert any("differs from the SHA-256 in DS2's manifest" in p for p in _problems(items))


def test_non_pdf_and_non_docx_are_rejected(tmp_path):
    (tmp_path / "pone.0047149.pdf").write_bytes(b"<html>blocked</html>")
    (tmp_path / "pone.0047149.s002.docx").write_bytes(b"<html>blocked</html>")
    text = " ".join(_problems(marsden.plan(tmp_path)))
    assert "not a PDF" in text and "cannot be opened" in text


@pytest.mark.skipif(
    not all((marsden.default_dir() / n).exists() for n in marsden.DS2_FILES),
    reason="the Marsden originals are not on this machine",
)
def test_the_real_ds2_originals_match_the_manifest():
    items = marsden.plan()
    assert all(i.checks.ok for i in items), _problems(items)
    names = {i.key_name or i.path.name for i in items}
    assert "MANIFEST.json" in names and "pone.0047149.pdf" in names
