"""DS1: Load expected outcomes and CDL agreement matrix for the backend.

This script does three things needed by the backend (Critical 2 and F5):
1. Expected outcomes per field (strategy_worth_exploring vs abstention)
2. CDL confusion matrix (agreement between DS1 labels and DE labels)
3. HLS value test (compare NDVI between corn and soybean years)

Usage: uv run python -m transform.ds1_backend_handover --load
"""
from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

# From the DE's field_selection_notes.csv
EXPECTED_CLASS_MAP = {
    "rotation": "strategy_worth_exploring",
    "continuous_corn": "abstention",
    "pasture_hay": "abstention",
    "mixed": "abstention",
}

# Our Phase 3 rule version
RULE_VERSION = "2026-11-14.1"


def build_expected_outcomes(crop_rotation_df: pd.DataFrame) -> pd.DataFrame:
    """Build expected_outcomes table: field_id -> expected engine result."""
    rows = []
    for _, row in crop_rotation_df.iterrows():
        field_class = row["field_class"]
        expected = EXPECTED_CLASS_MAP.get(field_class, "abstention")
        rows.append({
            "field_id": row["field_id"],
            "expected_outcome": expected,
            "basis": f"DS1 Phase 3 rules v{RULE_VERSION}: field_class={field_class}",
            "field_class": field_class,
        })
    return pd.DataFrame(rows)


def build_cdl_agreement(
    crop_rotation_df: pd.DataFrame,
    field_notes: pd.DataFrame,
) -> pd.DataFrame:
    """Build CDL agreement matrix comparing DS1 labels vs DE labels."""
    merged = crop_rotation_df.merge(
        field_notes[["field_id", "cdl_class"]],
        on="field_id",
        how="left",
    )
    merged["match"] = merged["field_class"] == merged["cdl_class"]
    
    # Per-class counts
    agreement = merged.groupby(["field_class", "cdl_class"]).size().reset_index(name="n_fields")
    
    return agreement


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--load", action="store_true", help="load into ClickHouse")
    args = parser.parse_args(argv)

    from common.config import clickhouse_client
    from common.load import load
    from common.migrate import migrate

    client = clickhouse_client()
    print("1. Reading crop_rotation from ClickHouse...")
    rotation = client.query_df("SELECT * FROM crop_rotation")
    print(f"   {len(rotation)} field rotation records")

    # Step 1: Expected outcomes
    print("\n2. Building expected outcomes...")
    expected = build_expected_outcomes(rotation)
    print(f"   {len(expected)} fields mapped")
    for _, r in expected.iterrows():
        print(f"     {r['field_id']}: {r['expected_outcome']} ({r['field_class']})")

    # Step 2: CDL agreement matrix
    print("\n3. Building CDL agreement matrix...")
    try:
        fields_df = client.query_df("SELECT field_id, domain_note FROM fields")
        agreement = build_cdl_agreement(rotation, fields_df)
        print(f"   Agreement matrix: {len(agreement)} class pairs")
        for _, r in agreement.iterrows():
            print(f"     DS1={r['field_class']:20s} vs DE={r['cdl_class']:20s}: {r['n_fields']} fields")
    except Exception as e:
        print(f"   Could not build agreement: {e}")

    # Step 3: HLS value test
    print("\n4. Running HLS vs CDL value test...")
    try:
        hls_ndvi = client.query_df(
            "SELECT field_id, ndvi_mean, acquired FROM hls_ndvi"
        )
        crop_history = client.query_df(
            "SELECT field_id, year, dominant_group FROM crop_history"
        )
        if not hls_ndvi.empty and not crop_history.empty:
            hls_ndvi["year"] = pd.to_datetime(hls_ndvi["acquired"]).dt.year
            crop_history["year"] = crop_history["year"].astype(int)
            merged = hls_ndvi.merge(
                crop_history[["field_id", "year", "dominant_group"]],
                on=["field_id", "year"],
            )
            merged = merged[merged["dominant_group"].isin(["corn", "soybeans"])]
            if len(merged) >= 10:
                corn = merged[merged["dominant_group"] == "corn"]["ndvi_mean"]
                soy = merged[merged["dominant_group"] == "soybeans"]["ndvi_mean"]
                diff = abs(float(corn.mean()) - float(soy.mean()))
                print(f"   Corn mean NDVI: {corn.mean():.4f}")
                print(f"   Soy mean NDVI: {soy.mean():.4f}")
                print(f"   Difference: {diff:.4f}")
                if diff > 0.05:
                    print("   CONCLUSION: HLS adds value (NDVI distinguishes corn from soy)")
                else:
                    print("   CONCLUSION: HLS does not clearly add value beyond CDL")
            else:
                print(f"   Insufficient data for value test: {len(merged)} observations")
        else:
            print(f"   Missing data: hls_ndvi={len(hls_ndvi)}, crop_history={len(crop_history)}")
    except Exception as e:
        print(f"   Value test error: {e}")

    # Load
    if args.load:
        print("\n5. Loading to ClickHouse...")
        try:
            applied = migrate(client)
            if applied:
                print(f"   Applied: {', '.join(applied)}")
            r = load(client, "engine_test_set", expected)
            print(f"   Loaded expected outcomes: {r.rows} rows")
            print("\n   Backend can now query: engine_test_set")
        except Exception as e:
            print(f"   LOAD ERROR: {e}")
            return 1
    else:
        print("\n   Dry run. Use --load to push to ClickHouse.")

    return 0


if __name__ == "__main__":
    sys.exit(main())