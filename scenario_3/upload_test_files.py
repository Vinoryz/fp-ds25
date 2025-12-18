from minio import Minio
from minio.error import S3Error
import hashlib
import os

# Initialize client
client = Minio(
    "localhost:9000",
    access_key="admin",
    secret_key="password123",
    secure=False
)

# Create bucket
bucket_name = "testbucket"
try:
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        print(f"✓ Bucket '{bucket_name}' created")
    else:
        print(f"✓ Bucket '{bucket_name}' already exists")
except S3Error as e:
    print(f"Error:  {e}")

# Generate and upload 20 test files
checksums = {}
for i in range(1, 21):
    filename = f"testfile_{i}.dat"
    # Create 10MB file
    size = 10 * 1024 * 1024
    data = os.urandom(size)
    
    # Calculate checksum
    md5 = hashlib.md5(data).hexdigest()
    checksums[filename] = md5
    
    # Write to temp file
    temp_path = f"/tmp/{filename}"
    with open(temp_path, "wb") as f:
        f.write(data)
    
    # Upload
    try: 
        client.fput_object(bucket_name, filename, temp_path)
        print(f"✓ Uploaded {filename} (MD5: {md5[: 8]}...)")
    except S3Error as e:
        print(f"✗ Failed to upload {filename}: {e}")
    
    # Cleanup
    os.remove(temp_path)

# Save checksums (format: filename<SPACE>md5)
with open("checksums.txt", "w") as f:
    for name, md5 in checksums. items():
        f.write(f"{name} {md5}\n")

print(f"\n✓ All 20 files uploaded.  Checksums saved to checksums. txt")
print(f"Total:  {len(checksums)} files")