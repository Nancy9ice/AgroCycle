"""DS1: Load expected outcomes and CDL agreement matrix for the backend.
Creates the engine_test_set table if it does not exist.
"""
from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_CLASS_MAP = {
    "rotation": "strategy_worth_exploring",
    "continuous_corn": "abstention",
    "pasture_hay": "abstention",
    "mixed": "abstention",
}
RULE_VERSION = "2026-11-14.1"

ENGINE_TEST_SET_DDL = """
CREATE TABLE IF NOT EXISTS engine_test_set (
    field_id                String,
    expected_outcome        Enum8('strategy_worth_exploring' = 1,
                                  'qualified_comparison' = 2,
                                  'abstention' = 3),
    basis                   String,
    field_class             LowCardinality(String),
    loaded_at               DateTime64(3, 'UTC') DEFAULT now64(3)
) ENGINE = MergeTree
ORDER BY (field_id)
"""


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--load", action="store_true")
    args = parser.parse_args(argv)

    from common.config import clickhouse_client
    
    client = clickhouse_client()
    print("1. Reading crop_rotation from ClickHouse...")
    rotation = client.query_df("SELECT * FROM crop_rotation")
    print(f"   {len(rotation)} field rotation records")

    # Step 1: Expected outcomes
    print("\n2. Building expected outcomes...")
    rows = []
    for _, row in rotation.iterrows():
        field_class = row["field_class"]
        expected = EXPECTED_CLASS_MAP.get(field_class, "abstention")
        rows.append({
            "field_id": row["field_id"],
            "expected_outcome": expected,
            "basis": f"DS1 Phase 3 rules v{RULE_VERSION}: field_class={field_class}",
            "field_class": field_class,
        })
    expected_df = pd.DataFrame(rows)
    print(f"   {len(expected_df)} fields mapped")
    for _, r in expected_df.iterrows():
        print(f"     {r['field_id']}: {r['expected_outcome']} ({r['field_class']})")

    # Step 2: CDL agreement (compare with DE's field_selection_notes)
    print("\n3. Building CDL agreement matrix...")
    try:
        de_notes = client.query_df(
            "SELECT field_id, domain_note FROM fields WHERE domain_note != ''"
        )
        if not de_notes.empty:
            de_notes["de_class"] = de_notes["domain_note"].str.extract(
                r"(rotation|continuous_corn|pasture_hay|mixed)"
            )
            merged = rotation.merge(de_notes[["field_id", "de_class"]], on="field_id", how="left")
            merged["match"] = merged["field_class"] == merged["de_class"]
            agreement = merged.groupby(["field_class", "de_class"]).size().reset_index(name="n_fields")
            print(f"   CDL Agreement: {len(agreement)} class pairs")
            for _, r in agreement.iterrows():
                match_status = "MATCH" if r["field_class"] == r["de_class"] else "DIFF"
                print(f"     DS1={r['field_class']:20s} vs DE={r['de_class']:20s}: {r['n_fields']} fields [{match_status}]")
            n_match = merged["match"].sum()
            print(f"\n   Total agreement: {n_match}/{len(merged)} fields")
        else:
            print("   No domain notes found in fields table")
    except Exception as e:
        print(f"   Agreement error: {e}")

    # Step 3: HLS value test
    print("\n4. Running HLS vs CDL value test...")
    try:
        hls_ndvi = client.query_df("SELECT field_id, ndvi_mean, acquired FROM hls_ndvi")
        crop_history = client.query_df("SELECT field_id, year, dominant_group FROM crop_history")
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
                print(f"   Corn mean NDVI: {corn.mean():.4f} (n={len(corn)} observations)")
                print(f"   Soy mean NDVI: {soy.mean():.4f} (n={len(soy)} observations)")
                print(f"   Difference: {diff:.4f}")
                if diff > 0.05:
                    print("   CONCLUSION: HLS adds value (NDVI clearly distinguishes corn from soy)")
                else:
                    print("   CONCLUSION: HLS does not clearly add value beyond CDL for field classification")
                    print("   HLS may still be useful for within-season monitoring (bare-field windows)")
            else:
                print(f"   Insufficient data: {len(merged)} observations")
        else:
            print(f"   Missing data")
    except Exception as e:
        print(f"   Value test error: {e}")

    if args.load:
        print("\n5. Loading to ClickHouse...")
        try:
            # Create table if it does not exist
            client.command(ENGINE_TEST_SET_DDL)
            print("   engine_test_set table ensured")
            
            # Clear old rows
            client.command("ALTER TABLE engine_test_set DELETE WHERE 1=1")
            
            # Insert
            client.insert(
                "engine_test_set",
                expected_df.values.tolist(),
                column_names=list(expected_df.columns),
            )
            count = client.query("SELECT count() FROM engine_test_set").result_rows[0][0]
            print(f"   Loaded {count} rows into engine_test_set")
            print("\n   Backend can now query: engine_test_set")
            print("   Schema: field_id, expected_outcome, basis, field_class, loaded_at")
        except Exception as e:
            print(f"   LOAD ERROR: {e}")
            return 1
    else:
        print("\n   Dry run. Use --load to push to ClickHouse.")

    return 0


if __name__ == "__main__":
    sys.exit(main())