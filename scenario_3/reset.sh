#!/bin/bash
echo "=== RESETTING ENTIRE ENVIRONMENT ==="

# Stop containers
echo "Stopping containers..."
docker-compose down

# Remove volumes
echo "Removing volumes..."
docker volume rm -f minio-lab_minio1-data 2>/dev/null
docker volume rm -f minio-lab_minio2-data 2>/dev/null
docker volume rm -f minio-lab_minio3-data 2>/dev/null
docker volume rm -f minio-lab_minio4-data 2>/dev/null
docker volume rm -f minio-lab_minio5-data 2>/dev/null
docker volume rm -f minio-lab_minio6-data 2>/dev/null

# Clean local files
echo "Cleaning local files..."
rm -f checksums.txt
rm -f log_*.txt
rm -f /tmp/*during_failure*
rm -f /tmp/*testfile*
rm -f /tmp/download_*.dat

echo "✓ Reset complete!"
echo ""
echo "Next:  docker-compose up -d"