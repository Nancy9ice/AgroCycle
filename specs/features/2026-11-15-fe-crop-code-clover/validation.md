# Validation

- `pytest tests/test_crop_rules.py tests/test_crop_history_build.py` pass with the `U` token.
- Full suite and `grep` show no remaining claim that `L` is low confidence (results recorded below after the run).

## Result (2026-11-15)

- `tests/test_crop_rules.py`, `api/`, `engine/`: 182 passed.
- `tests/test_crop_history_build.py` could not be collected here (geopandas not installed in the checking environment). The one assertion changed (`label.token == "U"`) was run directly against `rules.label_year` and holds. DE should run the full suite with `make test`.
