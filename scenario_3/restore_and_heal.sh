#!/bin/bash
echo "  RESTORE DISK & HEALING"
echo ""

# Restore disk by renaming back
echo "Step 1: Restoring disk on minio3..."

# FIX:  Tidak pakai grep di dalam container
docker exec minio3 sh -c '
cd /data || exit 1
for item in $(ls -A); do
    # Check if ends with .RENAMED
    case "$item" in
        *.RENAMED)
            original="${item%.RENAMED}"
            mv "$item" "$original" 2>/dev/null && echo "  ✓ Restored: $original" || echo "  ✗ Failed: $item"
            ;;
    esac
done
'

echo ""
echo "Disk structure AFTER restore:"
docker exec minio3 ls -la /data/
echo ""

echo "Step 2: Restarting minio3..."
docker restart minio3
sleep 20
echo "✓ minio3 restarted"
echo ""

echo "=== HEALING STATUS ==="
mc admin heal myminio --verbose

echo ""
echo "=== OBSERVASI 3: Apakah cluster rekonstruksi shards yang hilang? ==="
docker logs minio3 2>&1 | tail -50 | grep -iE "heal|reconstruct|repair|recover"

echo ""
echo "=== FINAL CLUSTER STATUS ==="
mc admin info myminio