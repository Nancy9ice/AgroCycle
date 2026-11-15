"""The web app carries a copy of the rule table and a parity fixture exported from this engine.

If DS2 changes a rule and nobody re-runs the export, the web app keeps rendering the old rules while
the API serves the new ones. The web test suite cannot notice (it compares two generated files), so this
test does. Fix: `cd web && npm run sync:engine`, then commit the regenerated files.
"""
import json
from pathlib import Path

from engine.rules import strategy_rules as rules

DATA = Path(__file__).resolve().parents[2] / "web" / "src" / "features" / "compare" / "data"


def _exported(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def test_exported_rule_table_matches_the_engine():
    table = _exported("rules.generated.json")
    assert table["rulesVersion"] == rules.RULES_VERSION, "run `npm run sync:engine` in web/"
    assert [r["rule_id"] for r in table["rules"]] == [r.rule_id for r in rules.APPLICABILITY_RULES]


def test_exported_parity_fixture_matches_the_engine_version():
    assert _exported("engine-parity.generated.json")["rulesVersion"] == rules.RULES_VERSION
