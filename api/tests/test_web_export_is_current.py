"""The web app carries a copy of the rule table and a parity fixture exported from this engine.

The API is the authoritative decision engine. The web app keeps a TypeScript copy only as a labelled offline
fallback, and that copy reads the exported files. If DS2 changes a rule, a sentence or the engine's logic and
nobody re-runs the export, the fallback keeps showing the old rules while the API serves the new ones. The web
test suite cannot notice (it compares two generated files with each other), so this test does.

It re-runs the export in memory and compares everything, not just the version string: a reworded rule or a
changed outcome with the same RULES_VERSION fails here too.

Fix: `cd web && npm run sync:engine`, then commit the regenerated files.
"""
import importlib.util
import json
from pathlib import Path

import pytest

from engine.rules import strategy_rules as rules

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "web" / "src" / "features" / "compare" / "data"
EXPORT_SCRIPT = ROOT / "web" / "scripts" / "export_engine.py"

HINT = "The web app's copy of the engine is stale. Run `npm run sync:engine` in web/ and commit the result."


@pytest.fixture(scope="module")
def export():
    spec = importlib.util.spec_from_file_location("export_engine", EXPORT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _committed(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def _as_json(value: dict) -> dict:
    """What the export would write to disk: tuples become lists, exactly as json.dumps does."""
    return json.loads(json.dumps(value, ensure_ascii=False))


def test_exported_rule_table_matches_the_engine(export):
    committed = _committed("rules.generated.json")
    assert committed["rulesVersion"] == rules.RULES_VERSION, HINT
    assert committed == _as_json(export.export_rules()), HINT


def test_exported_parity_fixture_matches_the_engine(export):
    committed = _committed("engine-parity.generated.json")
    assert committed["rulesVersion"] == rules.RULES_VERSION, HINT
    assert committed == _as_json(export.export_parity()), HINT
