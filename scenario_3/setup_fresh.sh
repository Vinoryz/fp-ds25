#!/bin/bash
echo "=== FRESH SETUP ==="

# Start cluster
echo "Starting cluster..."
docker-compose up -d

# Wait for cluster formation
echo "Waiting for cluster formation (60s)..."
sleep 60

# Setup MinIO client
echo "Setting up MinIO client..."
mc alias set myminio http://localhost:9000 admin password123

# Create bucket
echo "Creating test bucket..."
mc mb myminio/testbucket --ignore-existing

# Verify cluster
echo ""
echo "=== CLUSTER STATUS ==="
mc admin info myminio

echo ""
echo "✓ Setup complete!"
echo "Next: python3 upload_test_files. py"