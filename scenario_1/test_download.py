import os
import sys
import time
import shutil
import logging
from datetime import datetime, timezone, timedelta
from minio import Minio
from minio.error import S3Error
from concurrent.futures import ThreadPoolExecutor, as_completed

def gmt7_converter(*args):
    tz_gmt7 = timezone(timedelta(hours=7))
    return datetime.now(tz_gmt7).timetuple()

logging.Formatter.converter = gmt7_converter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_download_results.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "password123"
BUCKET_NAME = "test-bucket"

DOWNLOAD_DIR = "downloaded_files"
PARALLEL_DOWNLOADS = 1

def initialize_minio_client():
    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )

def download_file(client, bucket_name, object_name, download_path, download_id):
    try:
        stat = client.stat_object(bucket_name, object_name)
        size_bytes = stat.size
        size_mb = size_bytes / (1024 * 1024)
        
        logging.info(f"[Download {download_id:02d}] Starting: {object_name} ({size_mb:.2f} MB)")
        
        start_time = time.time()
        
        client.fget_object(bucket_name, object_name, download_path)
        
        end_time = time.time()
        download_time = end_time - start_time
        speed_mbps = size_mb / download_time if download_time > 0 else 0
        
        logging.info(f"[Download {download_id:02d}] [SUCCESS] Finished in {download_time:.3f}s ({speed_mbps:.2f} MB/s)")
        
        return {
            'download_id': download_id,
            'object_name': object_name,
            'size_bytes': size_bytes,
            'download_time': download_time,
            'speed_mbps': speed_mbps,
            'status': 'success'
        }
    except Exception as e:
        logging.error(f"[Download {download_id:02d}] [FAILED] Error downloading {object_name}: {e}")
        return {
            'download_id': download_id,
            'object_name': object_name,
            'status': 'failed',
            'error': str(e)
        }

def run_download_tests():
    logging.info("=" * 60)
    logging.info("MINIO PARALLEL DOWNLOAD TEST - STARTING")
    logging.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"Parallel Downloads: {PARALLEL_DOWNLOADS}")
    logging.info("=" * 60)

    if os.path.exists(DOWNLOAD_DIR):
        logging.info(f"Cleaning directory: {DOWNLOAD_DIR}...")
        shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR)
    logging.info(f"Directory ready: {DOWNLOAD_DIR}")

    try:
        client = initialize_minio_client()
        
        logging.info(f"Listing objects in bucket '{BUCKET_NAME}'...")
        objects = client.list_objects(BUCKET_NAME, recursive=True)
        object_list = [obj.object_name for obj in objects][:PARALLEL_DOWNLOADS]
        
        if not object_list:
            logging.warning("No objects found to download. Test aborted.")
            return

        logging.info(f"Found {len(object_list)} objects. Starting pool...")
        logging.info("-" * 60)

        results = []
        total_start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=PARALLEL_DOWNLOADS) as executor:
            futures = []
            for i, obj_name in enumerate(object_list, 1):
                local_path = os.path.join(DOWNLOAD_DIR, obj_name)
                futures.append(executor.submit(download_file, client, BUCKET_NAME, obj_name, local_path, i))
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        total_end_time = time.time()
        total_wall_time = total_end_time - total_start_time
        
        logging.info("=" * 60)
        logging.info("PARALLEL DOWNLOAD TEST SUMMARY")
        logging.info("=" * 60)
        
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'failed']
        
        if successful:
            total_size_bytes = sum(r['size_bytes'] for r in successful)
            total_size_mb = total_size_bytes / (1024 * 1024)
            avg_individual_speed = sum(r['speed_mbps'] for r in successful) / len(successful)
            total_throughput = total_size_mb / total_wall_time
            
            logging.info(f"Successful downloads: {len(successful)}/{len(object_list)}")
            logging.info(f"Failed downloads: {len(failed)}")
            logging.info(f"Total data downloaded: {total_size_mb:.2f} MB")
            logging.info(f"Total wall-clock time: {total_wall_time:.3f} seconds")
            logging.info(f"Total throughput: {total_throughput:.2f} MB/s")
            logging.info(f"Average individual download time: {sum(r['download_time'] for r in successful) / len(successful):.3f} seconds")
            logging.info(f"Average individual download speed: {avg_individual_speed:.2f} MB/s")

        if failed:
            logging.info("\nErrors Detail:")
            for f in failed:
                logging.info(f" - ID {f['download_id']}: {f['error']}")

        logging.info("=" * 60)
        logging.info("TEST COMPLETED")
        logging.info("=" * 60)
        
    except S3Error as e:
        logging.error(f"MinIO S3 Error: {e}")
    except Exception as e:
        logging.error(f"Fatal error: {e}")

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
        
        run_download_tests()
        
    except KeyboardInterrupt:
        logging.info("\nTest interrupted by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}")