import os
import sys
import time
from datetime import datetime, timezone, timedelta
from minio import Minio
from minio.error import S3Error
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

def gmt7_converter(*args):
    tz_gmt7 = timezone(timedelta(hours=7))
    return datetime.now(tz_gmt7).timetuple()

logging.Formatter.converter = gmt7_converter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_upload_results.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "password123"
BUCKET_NAME = "test-bucket"

TEST_FILE = "data_test_200mb.txt"
PARALLEL_UPLOADS = 10

upload_counter = threading.Lock()
upload_number = 0


def initialize_minio_client():
    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )
    return client


def create_bucket_if_not_exists(client, bucket_name):
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            logging.info(f"Bucket '{bucket_name}' created successfully")
        else:
            logging.info(f"Bucket '{bucket_name}' already exists")
    except S3Error as e:
        logging.error(f"Error creating bucket: {e}")
        raise


def get_file_size(filepath):
    size_bytes = os.path.getsize(filepath)
    size_mb = size_bytes / (1024 * 1024)
    return size_bytes, f"{size_mb:.2f} MB"


def upload_file(client, bucket_name, file_path, upload_id):
    global upload_number
    
    if not os.path.exists(file_path):
        logging.warning(f"File not found: {file_path}")
        return None
    
    file_name = os.path.basename(file_path)
    object_name = f"{upload_id:02d}_{file_name}"
    size_bytes, size_formatted = get_file_size(file_path)
    
    logging.info(f"[Upload {upload_id}] Starting: {object_name} ({size_formatted})")
    
    try:
        start_time = time.time()
        
        client.fput_object(
            bucket_name,
            object_name,
            file_path
        )
        
        end_time = time.time()
        upload_time = end_time - start_time
        
        speed_mbps = (size_bytes / (1024 * 1024)) / upload_time if upload_time > 0 else 0
        
        logging.info(f"[Upload {upload_id:02d}] [SUCCESS] Finished in {upload_time:.3f}s ({speed_mbps:.2f} MB/s)")
       
        return {
            'upload_id': upload_id,
            'file': object_name,
            'size_bytes': size_bytes,
            'size_formatted': size_formatted,
            'upload_time': upload_time,
            'speed_mbps': speed_mbps,
            'status': 'success'
        }
        
    except S3Error as e:
        logging.error(f"[Upload {upload_id}] [FAILED] Upload failed: {object_name} - {e}")
        return {
            'upload_id': upload_id,
            'file': object_name,
            'status': 'failed',
            'error': str(e)
        }


def run_upload_tests():
    logging.info("=" * 60)
    logging.info("MINIO PARALLEL UPLOAD TEST - STARTING")
    logging.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"MinIO Endpoint: {MINIO_ENDPOINT}")
    logging.info(f"Bucket: {BUCKET_NAME}")
    logging.info(f"Test File: {TEST_FILE}")
    logging.info(f"Parallel Uploads: {PARALLEL_UPLOADS}")
    logging.info("=" * 60)
    
    try:
        client = initialize_minio_client()
        logging.info("MinIO client initialized successfully")
        
        create_bucket_if_not_exists(client, BUCKET_NAME)
        
        results = []
        total_start_time = time.time()
        
        logging.info(f"Starting {PARALLEL_UPLOADS} parallel uploads...")
        logging.info("-" * 60)
        
        with ThreadPoolExecutor(max_workers=PARALLEL_UPLOADS) as executor:
            futures = []
            for i in range(1, PARALLEL_UPLOADS + 1):
                future = executor.submit(upload_file, client, BUCKET_NAME, TEST_FILE, i)
                futures.append(future)
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)
        
        total_end_time = time.time()
        total_time = total_end_time - total_start_time
        
        logging.info("=" * 60)
        logging.info("PARALLEL UPLOAD TEST SUMMARY")
        logging.info("=" * 60)
        
        successful_uploads = [r for r in results if r.get('status') == 'success']
        failed_uploads = [r for r in results if r.get('status') == 'failed']
        
        if successful_uploads:
            total_size = sum(r['size_bytes'] for r in successful_uploads)
            total_upload_time = sum(r['upload_time'] for r in successful_uploads)
            
            successful_uploads.sort(key=lambda x: x['upload_id'])
            
            avg_individual_time = total_upload_time / len(successful_uploads)
            avg_individual_speed = sum(r['speed_mbps'] for r in successful_uploads) / len(successful_uploads)
            total_throughput = (total_size / (1024 * 1024)) / total_time if total_time > 0 else 0
            
            logging.info(f"Successful uploads: {len(successful_uploads)}/{PARALLEL_UPLOADS}")
            logging.info(f"Failed uploads: {len(failed_uploads)}")
            logging.info(f"Total data uploaded: {total_size / (1024 * 1024):.2f} MB")
            logging.info(f"Total wall-clock time: {total_time:.3f} seconds")
            logging.info(f"Total throughput: {total_throughput:.2f} MB/s")
            logging.info(f"Average individual upload time: {avg_individual_time:.3f} seconds")
            logging.info(f"Average individual upload speed: {avg_individual_speed:.2f} MB/s")
                               
        if failed_uploads:
            logging.info("\nFailed uploads:")
            for r in failed_uploads:
                logging.info(f"  Upload {r['upload_id']:02d}: {r.get('error', 'Unknown error')}")
        
        logging.info("=" * 60)
        logging.info("TEST COMPLETED")
        logging.info("=" * 60)
        
    except Exception as e:
        logging.error(f"Test failed with error: {e}")
        raise

def log_custom_title(title):
    logging.info("=" * 60)
    logging.info(f"{title}")
    logging.info("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        scenario_title = sys.argv[1]
    else:
        scenario_title = "No Title Provided"

    try:
        log_custom_title(scenario_title)
        
        run_upload_tests()
        
    except KeyboardInterrupt:
        logging.info("\nTest interrupted by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
