"""Compare Phase 3 results with DE's original labels."""
import pandas as pd

ours = pd.read_csv('data/out/phase3/cdl_rotation_summary.csv')
notes = pd.read_csv('data/fields/field_selection_notes.csv')
merged = ours.merge(notes[['field_id', 'cdl_class']], on='field_id')
merged['match'] = merged['rotation_class'] == merged['cdl_class']

# Also load the history for sequences
hist = pd.read_csv('data/out/phase3/cdl_crop_history.csv')
seqs = {}
for fid in hist['field_id'].unique():
    fdf = hist[hist['field_id']==fid].sort_values('year')
    seqs[fid] = "".join({"corn":"C","soybean":"S","pasture":"P","mixed":"M","oats":"O","alfalfa":"A","other":"X","no_data":"N"}.get(r['dominant_crop'],"?") for _, r in fdf.iterrows())

print("COMPARISON: DS1 (Phase 3) vs DE (original labels)")
print("="*70)
print(f"Matching: {merged['match'].sum()}/{len(merged)} fields")
print(f"Differences: {(~merged['match']).sum()}/{len(merged)} fields")
print()

mismatches = merged[~merged['match']]
if len(mismatches) > 0:
    print(f"{'Field ID':20s} {'DS1 (Phase 3)':22s} {'DE (original)':20s} {'Sequence':15s}")
    print("-"*80)
    for _, r in mismatches.iterrows():
        seq = seqs.get(r['field_id'], "?")
        print(f"{r['field_id']:20s} {r['rotation_class']:22s} {r['cdl_class']:20s} {seq:15s}")

print()
print("--- Count summary ---")
print(f"DE rotation: {(notes.cdl_class=='rotation').sum()} | DS1 rotation: {(merged.rotation_class=='rotation').sum()}")
print(f"DE corn: {(notes.cdl_class=='corn').sum()} | DS1 continuous_corn: {(merged.rotation_class=='continuous_corn').sum()}")
print(f"DE pasture: {(notes.cdl_class=='pasture').sum()} | DS1 pasture_hay: {(merged.rotation_class=='pasture_hay').sum()}")
print(f"DE mixed: {(notes.cdl_class=='mixed').sum()} | DS1 mixed: {(merged.rotation_class=='mixed').sum()}")