import os
import time
import subprocess
import glob
import argparse
from minio import Minio
import datetime

# --- Configuration ---
MINIO_ENDPOINT = "localhost:9000"
ACCESS_KEY = "admin"
SECRET_KEY = "password123"
BUCKET_NAME = "scenario2-bucket"
TEST_DATA_DIR = "./test_data"

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
        # Basic check
        if not client.bucket_exists(BUCKET_NAME):
             client.make_bucket(BUCKET_NAME)
             print(f"[INFO] Bucket '{BUCKET_NAME}' created.")
        return client
    except Exception as e:
        print(f"[ERROR] Failed to connect: {e}")
        exit(1)

def load_test_data(source_dir):
    """Load list of files to upload from local directory"""
    if not os.path.exists(source_dir):
        print(f"[ERROR] Directory '{source_dir}' not found.")
        exit(1)
    files = glob.glob(os.path.join(source_dir, "*"))
    if not files:
        print(f"[ERROR] No files found in '{source_dir}'.")
        exit(1)
    return files

def clear_bucket(minioClient):
    """Delete all objects in the bucket"""
    print(f"\n[STEP] Clearing bucket '{BUCKET_NAME}'...")
    try:
        if not minioClient.bucket_exists(BUCKET_NAME):
            print("[INFO] Bucket does not exist, nothing to clear.")
            return

        objects = list(minioClient.list_objects(BUCKET_NAME, recursive=True))
        # Konversi ke dictionary
        import json
        objects_data = []
        for obj in objects:
            objects_data.append({
                "object_name": obj.object_name,
                "size": obj.size,
                "last_modified": str(obj.last_modified),
                "etag": obj.etag
            })
        # Tulis ke file JSON
        with open("objects_list.json", "w") as f:
            json.dump(objects_data, f, indent=2)

        
        if not objects:
            print("[INFO] Bucket is already empty.")
            return

        for obj in objects:
            minioClient.remove_object(BUCKET_NAME, obj.object_name)
            
        print(f"[INFO] Removed {len(objects)} objects.")
    except Exception as e:
        print(f"[WARN] Failed to clear bucket: {e}")

def upload_files(minioClient, prefix):
    """Upload files to MinIO"""
    files = load_test_data(TEST_DATA_DIR)
    print(f"\n[STEP] Uploading {len(files)} files with prefix '{prefix}'...")
    
    success_count = 0
    start_time = time.time()
    
    for file_path in files:
        file_name = os.path.basename(file_path)
        object_name = f"{prefix}/{file_name}"
        try:
            minioClient.fput_object(BUCKET_NAME, object_name, file_path)
            print(f"   + Uploaded: {object_name}")
            success_count += 1
        except Exception as e:
            print(f"   X Failed to upload {file_name}: {e}")
    
    elapsed = time.time() - start_time
    print(f"[RESULT] Uploaded {success_count}/{len(files)} files in {elapsed:.2f}s")

def download_files(minioClient, prefix, count):
    """Read files from MinIO"""
    print(f"\n[STEP] Reading max {count} files with prefix '{prefix}'...")
    success_count = 0
    
    objects = list(minioClient.list_objects(BUCKET_NAME, prefix=prefix, recursive=True))
    targets = objects[:count]
    
    if not targets:
        print(f"[WARN] No objects found with prefix '{prefix}'.")
        return

    start_time = time.time()
    
    for obj in targets:
        try:
            data = minioClient.get_object(BUCKET_NAME, obj.object_name)
            data.read() 
            data.close()
            data.release_conn()
            print(f"   + Read Success: {obj.object_name}", flush=True)
            success_count += 1
        except Exception as e:
            print(f"   X Read error {obj.object_name}: {e}", flush=True)
    
    elapsed = time.time() - start_time
    print(f"[RESULT] Successfully read {success_count}/{len(targets)} files in {elapsed:.2f}s")

def contain_operation(command, container_name):
    """Run docker command"""
    print(f"\n[ACTION] Executing: docker {command} {container_name}")
    try:
        print(f"[TIME] Current UTC: {datetime.datetime.now(datetime.timezone.utc)}")
        subprocess.run(["docker", command, container_name], check=True)
        print(f"[INFO] Successfully {command}ed {container_name}.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Docker command failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="Interactive MinIO Scenario 2 Tester")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: clear
    subparsers.add_parser("clear", help="Clear all objects in the bucket")

    # Command: upload
    parser_upload = subparsers.add_parser("upload", help="Upload files from test_data")
    parser_upload.add_argument("--prefix", default="data", help="Prefix for object names (folder)")

    # Command: read
    parser_read = subparsers.add_parser("read", help="Read files from bucket")
    parser_read.add_argument("--prefix", default="data", help="Prefix of objects to read")
    parser_read.add_argument("--count", type=int, default=5, help="Number of files to read")

    # Command: stop
    parser_stop = subparsers.add_parser("stop", help="Stop a docker container node")
    parser_stop.add_argument("--node", default="minio3", help="Container name to stop")

    # Command: start
    parser_start = subparsers.add_parser("start", help="Start a docker container node")
    parser_start.add_argument("--node", default="minio3", help="Container name to start")

    args = parser.parse_args()

    # Determine need for client connection (docker ops don't valid minio connection strictly speaking, but fine to have)
    if args.command in ["clear", "upload", "read"]:
        client = connect_client()

    if args.command == "clear":
        clear_bucket(client)
    elif args.command == "upload":
        upload_files(client, prefix=args.prefix)
    elif args.command == "read":
        download_files(client, prefix=args.prefix, count=args.count)
    elif args.command == "stop":
        contain_operation("stop", args.node)
    elif args.command == "start":
        contain_operation("start", args.node)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
