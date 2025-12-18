from minio import Minio
from minio.error import S3Error
import hashlib
import os
import sys

client = Minio("localhost:9000", 
               access_key="admin", 
               secret_key="password123",
               secure=False)

# Load original checksums
checksums = {}
try:
    with open("checksums.txt", "r") as f:
        for line in f: 
            line = line.strip()
            if not line:
                continue
            # Split only once from right (handle spaces in filename)
            parts = line.rsplit(' ', 1)
            if len(parts) == 2:
                name, md5 = parts
                checksums[name] = md5
            else:
                print(f"⚠ Skipping invalid line: {line}")
except FileNotFoundError:
    print("✗ checksums.txt not found!  Run upload_test_files.py first.")
    sys.exit(1)

if not checksums:
    print("✗ No checksums loaded.  Check checksums.txt format.")
    sys.exit(1)

print(f"Loaded {len(checksums)} checksums to verify\n")

# Verify each file
errors = 0
verified = 0

for filename, original_md5 in checksums. items():
    try:
        # Download
        local_path = f"/tmp/verify_{filename}"
        client.fget_object("testbucket", filename, local_path)
        
        # Calculate MD5
        with open(local_path, "rb") as f:
            current_md5 = hashlib. md5(f.read()).hexdigest()
        
        if current_md5 == original_md5:
            print(f"✓ {filename} - integrity verified")
            verified += 1
        else:
            print(f"✗ {filename} - CORRUPTED!  (expected: {original_md5}, got: {current_md5})")
            errors += 1
        
        # Cleanup
        os.remove(local_path)
        
    except S3Error as e: 
        print(f"✗ {filename} - ERROR: {e}")
        errors += 1

print(f"\n{'='*50}")
print(f"Results: {verified} verified, {errors} errors")
print(f"{'✓ All files intact!' if errors == 0 else f'✗ {errors} files corrupted or missing'}")