import os
import time
import subprocess
import glob
import hashlib
from minio import Minio
from minio.error import S3Error
import datetime

# --- Configuration ---
MINIO_ENDPOINT = "localhost:9000"  # Assuming minio1 is exposed here
ACCESS_KEY = "admin"
SECRET_KEY = "password123"
BUCKET_NAME = "scenario2-bucket"
TEST_DATA_DIR = "./test_data" # Directory containing dummy files txt 10MB each

def connect_client():
    """Connect to MinIO Cluster"""
    print(f"[INFO] Connecting to MinIO at {MINIO_ENDPOINT}...")
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=ACCESS_KEY,
            secret_key=SECRET_KEY,
            secure=False
        )
        if not client.bucket_exists(BUCKET_NAME):
            client.make_bucket(BUCKET_NAME)
            print(f"[INFO] Bucket '{BUCKET_NAME}' created.")
        else:
            print(f"[INFO] Bucket '{BUCKET_NAME}' found.")
        return client
    except Exception as e:
        print(f"[ERROR] Failed to connect: {e}")
        exit(1)

def load_test_data(source_dir):
    """Load list of files to upload from local directory"""
    print(f"[INFO] Scanning for test data in '{source_dir}'...")
    if not os.path.exists(source_dir):
        print(f"[ERROR] Directory '{source_dir}' not found. Please create it and add dummy files.")
        exit(1)
    
    files = glob.glob(os.path.join(source_dir, "*"))
    if not files:
        print(f"[ERROR] No files found in '{source_dir}'.")
        exit(1)
        
    print(f"[INFO] Found {len(files)} files to test.")
    return files

def calculate_md5(file_path):
    """Calculate MD5 hash of a file"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def clear_bucket(minioClient):
    """Delete all objects in the bucket to start fresh"""
    print(f"\n[STEP] Clearing bucket '{BUCKET_NAME}'...")
    try:
        if not minioClient.bucket_exists(BUCKET_NAME):
            return

        # List all objects
        objects = list(minioClient.list_objects(BUCKET_NAME, recursive=True))
        if not objects:
            print("[INFO] Bucket is already empty.")
            return

        # Delete them
        for obj in objects:
            minioClient.remove_object(BUCKET_NAME, obj.object_name)
            
        print(f"[INFO] Removed {len(objects)} old objects.")
    except Exception as e:
        print(f"[WARN] Failed to clear bucket: {e}")

def upload_files(minioClient, files, prefix="baseline"):
    """Upload files to MinIO"""
    print(f"\n[STEP] Uploading {len(files)} files with prefix '{prefix}'...")
    
    # Cek apakah bucket ada, jika tidak buat baru
    if not minioClient.bucket_exists(BUCKET_NAME):
        minioClient.make_bucket(BUCKET_NAME)
        print(f"[INFO] Bucket '{BUCKET_NAME}' created.")
        
    success_count = 0
    start_time = time.time()
    
    for file_path in files:
        file_name = os.path.basename(file_path)
        object_name = f"{prefix}/{file_name}"
        try:
            minioClient.fput_object(BUCKET_NAME, object_name, file_path)
            print(f"   + Uploaded: {object_name}") 
            success_count += 1
        except Exception as e: print(f"   X Failed to upload {file_name}: {e}")
    
    elapsed = time.time() - start_time
    print(f"[RESULT] Uploaded {success_count}/{len(files)} files in {elapsed:.2f}s")
    return success_count

def download_files(minioClient, prefix="baseline", count=20):
    """Try to download files and verify CHECKSUM"""
    print(f"\n[STEP] Verifying Read Availability & INTEGRITY (Sample {count} files)...")
    success_count = 0
    
    start_time = time.time()
    # List objects to find candidates
    objects = list(minioClient.list_objects(BUCKET_NAME, prefix=prefix, recursive=True))
    
    # Take first N objects or all if less than N
    targets = objects[:count]
    if not targets:
        print("[WARN] No objects found to download.")
        return False

    for obj in targets:
        try:
            # 1. Get object stream
            print(f"[TIME] [BEFORE GET OBJECT]Current UTC: {datetime.datetime.now(datetime.timezone.utc)}")
            data = minioClient.get_object(BUCKET_NAME, obj.object_name)
            print(f"[TIME] [AFTER GET OBJECT]Current UTC: {datetime.datetime.now(datetime.timezone.utc)}")
            content = data.read()
            data.close()
            data.release_conn()

            # 2. Calculate hash of downloaded content
            downloaded_md5 = hashlib.md5(content).hexdigest()

            # 3. Find original file to compare
            # Assuming object_name format is "prefix/filename"
            original_filename = os.path.basename(obj.object_name)
            original_path = os.path.join(TEST_DATA_DIR, original_filename)
            
            if os.path.exists(original_path):
                original_md5 = calculate_md5(original_path)
                if downloaded_md5 == original_md5:
                    print(f"   + Verified: {obj.object_name} (MD5 Match)")
                    success_count += 1
                else:
                    print(f"   ! CORRUPT: {obj.object_name} (Hash Mismatch!)")
            else:
                # If original file missing (e.g. create in another phase), simplify just OK
                print(f"   + Read Success: {obj.object_name} (No local file to verify)")
                success_count += 1

        except Exception as e:
            print(f"   X Read error {obj.object_name}: {e}")

    elapsed = time.time() - start_time
    print(f"[RESULT] Successfully verified {success_count}/{len(targets)} files in {elapsed:.2f}s")
    return success_count == len(targets)

def contain_operation(command, container_name):
    """Run docker command"""
    print(f"\n[ACTION] Executing: docker {command} {container_name}")
    try:
        print(f"[TIME] Current UTC: {datetime.datetime.now(datetime.timezone.utc)}")
        subprocess.run(["docker", command, container_name], check=True)
        print(f"[INFO] Container {container_name} {command}ed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Docker command failed: {e}")
        exit(1)

def main():
    print("=== SCENARIO 2: Node Failure & Self-Healing ===\n")
    
    # 1. Setup
    minioClient = connect_client()
    clear_bucket(minioClient) # Start fresh
    files = load_test_data(TEST_DATA_DIR)
    
    # 2. Baseline Upload (All nodes healthy)
    print("\n--- PHASE 1: Baseline Upload (All Nodes Healthy) ---")
    upload_files(minioClient, files, prefix="phase1")

    # 3. Baseline Read (All nodes healthy) - NEW PHASE
    print("\n--- PHASE 2: Baseline Read Verification (All Nodes Healthy) ---")
    download_files(minioClient, prefix="phase1", count=20)
    
    # 4. Simulate Failure for Read Availability (1 Note)
    print(f"\n--- PHASE 3: Simulating Failure 1 Node (Killing {"minio3"}) ---")
    contain_operation("stop", "minio3")
    
    # 5. Test Persistence & Availability when 1 node die
    print("\n--- PHASE 4: Testing Read Availability (1 Node Mati) ---")
    print("Trying to READ files uploaded in Phase 1...")
    download_files(minioClient, prefix="phase1", count=20)

    print("\n--- PHASE 5: Testing Read Availability - Steady State (1 Node Mati) ---")
    print("Trying to READ files uploaded in Phase 1 (Again)...")
    download_files(minioClient, prefix="phase1", count=20)
    
    # 6. Simulate Failure for Read Availability (2 Node)
    print(f"\n--- PHASE 6: Simulating Failure 2 Node (Killing {"minio5"}) ---")
    contain_operation("stop", "minio5")

    # 7. Test Persistence & Availability when 2 node die
    print("\n--- PHASE 7: Testing Read Availability (2 Node Mati) ---")
    print("Trying to READ files uploaded in Phase 1...")
    download_files(minioClient, prefix="phase1", count=20)

    print("\n--- PHASE 8: Testing Read Availability - Steady State (2 Node Mati) ---")
    print("Trying to READ files uploaded in Phase 1 (Again)...")
    download_files(minioClient, prefix="phase1", count=20)

    # 8. Simulate Failure for Read Availability (3 Node)
    print(f"\n--- PHASE 9: Simulating Failure 3 Node (Killing {"minio6"}) ---")
    contain_operation("stop", "minio6")

    # 9. Test Persistence & Availability when 3 node die
    print("\n--- PHASE 10: Testing Read Availability (3 Node Mati) ---")
    print("Trying to READ files uploaded in Phase 1...")
    download_files(minioClient, prefix="phase1", count=20)

    print("\n--- PHASE 11: Testing Read Availability - Steady State (3 Node Mati) ---")
    print("Trying to READ files uploaded in Phase 1 (Again)...")
    download_files(minioClient, prefix="phase1", count=20)

    # 10. Recovery node pertama yang di kill
    print(f"\n--- PHASE 12: Recovery (Reviving {"minio3"}) ---")
    contain_operation("start", "minio3")
    
    # 11. Recovery node kedua yang di kill
    print(f"\n--- PHASE 13: Recovery (Reviving {"minio5"}) ---")
    contain_operation("start", "minio5")

    # 12. Recovery node ketiga yang di kill
    print(f"\n--- PHASE 14: Recovery (Reviving {"minio6"}) ---")
    contain_operation("start", "minio6")
    """
    """

    print("\n=== EXPERIMENT COMPLETE ===")

if __name__ == "__main__":
    main()
