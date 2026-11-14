"""Check a CDL manifest and verify file integrity."""
import boto3, os, json

with open(".env") as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()

s3 = boto3.client("s3", region_name=os.environ["AWS_REGION"])
bucket = "agrocycle-fieldshift-2026-data"

# Read a manifest
key = "raw/cdl/annual-30m-website-export/2026-11-14/CDL_2023_19015.tif.manifest.json"
resp = s3.get_object(Bucket=bucket, Key=key)
manifest = json.loads(resp["Body"].read())
print("=== Manifest for CDL_2023_19015.tif ===")
print(json.dumps(manifest, indent=2))

# Also check the HLS manifest
key2 = "raw/hls/l30/v2.0/2026-11-14/primary-001/20230405/b04.tif.manifest.json"
resp2 = s3.get_object(Bucket=bucket, Key=key2)
manifest2 = json.loads(resp2["Body"].read())
print("\n=== Manifest for primary-001 HLS b04 ===")
print(json.dumps(manifest2, indent=2))