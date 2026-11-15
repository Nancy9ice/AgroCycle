"""Fix f-string lint errors in ds1_backend_handover.py - remove f prefix from strings without placeholders."""
with open("transform/ds1_backend_handover.py", "r") as f:
    c = f.read()
c = c.replace(
    'print(f" CONCLUSION: HLS adds value (NDVI distinguishes corn from soy)")',
    'print(" CONCLUSION: HLS adds value (NDVI distinguishes corn from soy)")'
)
c = c.replace(
    'print(f" CONCLUSION: HLS does not clearly add value beyond CDL")',
    'print(" CONCLUSION: HLS does not clearly add value beyond CDL")'
)
c = c.replace(
    'print(f"\\n Backend can now query: engine_test_set")',
    'print("\\n Backend can now query: engine_test_set")'
)
with open("transform/ds1_backend_handover.py", "w") as f:
    f.write(c)
print("Fixed f-string lint errors")