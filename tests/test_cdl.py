import pytest

from ingest import cdl


def _dummy_clips(base, skip=(), extra=()):
    """Empty stand-ins for the clips: find_files only looks at names."""
    folders = {"Story": "polygonclip_20261114042638_888481240",
               "Boone": "polygonclip_20261114043538_1366781222"}
    for county, fips in cdl.COUNTIES.items():
        (base / folders[county]).mkdir(parents=True, exist_ok=True)
        for year in cdl.YEARS:
            if (county, year) not in skip:
                (base / folders[county] / f"CDL_{year}_{fips}.tif").write_bytes(b"x")
    for name in extra:
        (base / folders["Story"] / name).write_bytes(b"x")


def test_find_files_returns_one_clip_per_county_and_year(tmp_path):
    _dummy_clips(tmp_path)
    found = cdl.find_files(tmp_path)
    assert len(found) == 22 and found[("Story", 2024)].name == "CDL_2024_19169.tif"


def test_missing_clip_is_reported(tmp_path):
    _dummy_clips(tmp_path, skip={("Boone", 2020)})
    with pytest.raises(RuntimeError, match="Boone 2020: expected 1 clip, found 0"):
        cdl.find_files(tmp_path)


def test_stray_clip_is_reported(tmp_path):
    _dummy_clips(tmp_path, extra=["CDL_2030_19169.tif"])
    with pytest.raises(RuntimeError, match="unexpected clip CDL_2030_19169.tif"):
        cdl.find_files(tmp_path)


def test_retrieval_date_comes_from_the_folder_name(tmp_path):
    folder = tmp_path / "polygonclip_20261114042638_888481240"
    folder.mkdir()
    assert cdl.retrieval_date(folder / "CDL_2015_19169.tif") == "2026-11-14"
    other = tmp_path / "random_folder"
    other.mkdir()
    with pytest.raises(ValueError):
        cdl.retrieval_date(other / "CDL_2015_19169.tif")


@pytest.mark.skipif(not cdl.default_dir().exists(), reason="CDL clips are not on this machine")
def test_plan_on_the_real_clips():
    items = cdl.plan()
    tifs = [i for i in items if i.path.suffix == ".tif"]
    assert len(items) == 44 and len(tifs) == 22
    assert all(i.checks.ok for i in items), [i.checks.problems for i in items if not i.checks.ok]
    resampled = [i for i in tifs if i.manifest.subset["resampled_from_10m"]]
    assert len(resampled) == 4 and all("resampled 30 m" in i.manifest.notes for i in resampled)
