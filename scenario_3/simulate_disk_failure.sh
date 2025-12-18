#!/bin/bash
echo "=========================================="
echo "  SKENARIO 3: DISK FAILURE SIMULATION"
echo "=========================================="
echo ""
echo "Langkah soal:"
echo "1. Hapus atau rename directory disk di satu node"
echo "2. Restart node tersebut"
echo ""

# BEFORE
echo "[BEFORE] Cluster Status:"
mc admin info myminio | tail -1
echo ""

# Check structure BEFORE
echo "Disk structure BEFORE:"
docker exec minio3 ls -la /data/
echo ""

# STEP 1: Rename all contents of /data
echo "=== STEP 1: Rename Directory Disk ==="
echo "Method:  Rename ALL contents inside /data"
echo ""

# FIX: Tambahkan cd /data
docker exec minio3 sh -c '
cd /data || exit 1
for item in $(ls -A); do
    mv "$item" "${item}.RENAMED" 2>/dev/null && echo "  ✓ Renamed: $item" || echo "  ✗ Failed: $item"
done
'

# Verify renaming
echo ""
echo "Disk structure AFTER rename:"
docker exec minio3 ls -la /data/
echo ""

# STEP 2: Restart node
echo "=== STEP 2: Restart Node ==="
docker restart minio3
sleep 20
echo "✓ minio3 restarted"
echo ""

# AFTER
echo "[AFTER] Cluster Status:"
mc admin info myminio

echo ""
echo "=== OBSERVASI 1: Apakah cluster deteksi disk failure?  ==="
echo "Expected: drives offline increased atau healing triggered"
mc admin info myminio | grep -E "drives online|drives offline"

echo ""
echo "minio3 specific status:"
mc admin info myminio | grep -A 4 "minio3:9000"

echo ""
echo "=== Check Logs for Disk Errors ==="
docker logs minio3 2>&1 | tail -50 | grep -iE "error|fail|format|disk|drive|heal" | head -20