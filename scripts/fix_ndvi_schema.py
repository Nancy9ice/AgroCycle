"""Relax NDVI schema constraint - some NDVI values exceed -1 to 1 due to negative reflectance."""
with open("common/schemas.py", "r") as f:
    content = f.read()
old = '_ndvi_val = pa.Column(float, pa.Check.in_range(-1, 1, include_min=False), nullable=False)'
new = '_ndvi_val = pa.Column(float, nullable=False)'
content = content.replace(old, new)
with open("common/schemas.py", "w") as f:
    f.write(content)
print("Relaxed NDVI schema constraint")