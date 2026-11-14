from ingest.checks import CheckResult
from ingest.items import Item, run_items
from ingest.manifest import build_manifest
from ingest.s3_store import raw_key
from tests.test_s3_store import FIELDS, FakeS3


def _item(tmp_path, problems=(), key_name=None):
    path = tmp_path / "data.csv"
    path.write_bytes(b"a,b\n1,2\n")
    return Item(path, build_manifest(path, **FIELDS), CheckResult(list(problems)), "power", key_name)


def test_failed_check_blocks_every_upload(tmp_path):
    client = FakeS3()
    items = [_item(tmp_path), _item(tmp_path, problems=["bad file"])]
    assert run_items(items, client, "bkt", execute=True) == 1
    assert client.objects == {}


def test_dry_run_writes_nothing_and_execute_uploads_and_verifies(tmp_path):
    client = FakeS3()
    item = _item(tmp_path)
    assert run_items([item], client, "bkt", execute=False) == 0
    assert client.objects == {}
    assert run_items([item], client, "bkt", execute=True) == 0
    assert raw_key("power", "v1", "2026-11-14", "data.csv") in client.objects


def test_second_run_skips_files_already_in_s3(tmp_path, capsys):
    client = FakeS3()
    item = _item(tmp_path)
    run_items([item], client, "bkt", execute=True)
    assert run_items([item], client, "bkt", execute=True) == 0
    assert "already in S3, skipped" in capsys.readouterr().out


def test_key_name_may_contain_folders(tmp_path):
    client = FakeS3()
    item = _item(tmp_path, key_name="primary-001/20230615/b04.tif")
    run_items([item], client, "bkt", execute=True)
    assert raw_key("power", "v1", "2026-11-14", "primary-001/20230615/b04.tif") in client.objects
