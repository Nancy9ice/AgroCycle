"""Fix NaN values in percentile/std calculations for phase5.py - use np.nanpercentile and fill any leftover NaN."""
with open("transform/hls/phase5.py", "r") as f:
    content = f.read()

content = content.replace(
    '"ndvi_p25": float(np.percentile(valid_ndvi, 25)),',
    '"ndvi_p25": float(np.nanpercentile(valid_ndvi, 25) or 0.0),'
)
content = content.replace(
    '"ndvi_p75": float(np.percentile(valid_ndvi, 75)),',
    '"ndvi_p75": float(np.nanpercentile(valid_ndvi, 75) or 0.0),'
)
content = content.replace(
    '"ndvi_std": float(np.nanstd(valid_ndvi)),',
    '"ndvi_std": float(np.nanstd(valid_ndvi) or 0.0),'
)
# Also ensure ndvi_mean and ndvi_median never produce NaN
content = content.replace(
    '"ndvi_mean": float(np.nanmean(valid_ndvi)),',
    '"ndvi_mean": float(np.nanmean(valid_ndvi) or 0.0),'
)
content = content.replace(
    '"ndvi_median": float(np.nanmedian(valid_ndvi)),',
    '"ndvi_median": float(np.nanmedian(valid_ndvi) or 0.0),'
)

with open("transform/hls/phase5.py", "w") as f:
    f.write(content)
print("Fixed all NaN issues in phase5.py")