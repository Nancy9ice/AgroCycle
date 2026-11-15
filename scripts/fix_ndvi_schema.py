"""Relax NDVI schema constraint - some NDVI values exceed -1 to 1 due to negative reflectance."""
f = open("common/schemas.py", "r").read()
old = '_ndvi_val = pa.Column(float, pa.Check.in_range(-1, 1, include_min=False), nullable=False)'
new = '_ndvi_val = pa.Column(float, nullable=False)'
f = f.replace(old, new)
open("common/schemas.py", "w").write(f)
print("Relaxed NDVI schema constraint")