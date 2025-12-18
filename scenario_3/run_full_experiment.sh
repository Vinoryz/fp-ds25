#!/bin/bash
set -e  # Exit on error

echo "  MINIO DISTRIBUTED STORAGE EXPERIMENT"
echo "  Skenario 3: Disk Failure & Recovery"
echo ""

echo "PHASE 0: Setting permissions..."
chmod +x reset.sh setup_fresh.sh simulate_disk_failure.sh
chmod +x test_simple.sh performance_test.sh restore_and_heal.sh
echo "✓ Permissions set"
echo ""

echo "PHASE 1: Measuring baseline performance..."
echo ""

# Setup
./reset.sh
./setup_fresh.sh
python3 upload_test_files.py

# Performance baseline
echo ""
echo "Measuring baseline performance..."
./performance_test.sh | tee log_performance_baseline.txt

# Cluster status
mc admin info myminio | tee log_status_baseline.txt

echo ""
echo "✓ Baseline captured"
echo ""

echo "PHASE 2: Simulating failure and testing..."
echo ""

# Simulate failure
./simulate_disk_failure.sh | tee log_failure.txt

echo ""
echo "✓ Failure simulated"
echo ""

# Wait a bit for cluster to react
echo "Waiting 10s for cluster to react..."
sleep 10

# Test operations DURING failure
echo "Testing operations with degraded cluster..."
./test_simple.sh | tee log_test_during.txt

# Performance during failure
echo ""
echo "Measuring performance during failure..."
./performance_test.sh | tee log_performance_during.txt

echo ""
echo "✓ During-failure tests complete"
echo ""

echo "PHASE 3: Restore and verify recovery..."
echo ""

# Wait for any ongoing healing
echo "Waiting 30s for healing to complete..."
sleep 30

# Restore
./restore_and_heal.sh | tee log_restore.txt

# Wait after restore
echo ""
echo "Waiting 20s after restore..."
sleep 20

# Verify integrity
echo ""
echo "Verifying data integrity..."
python3 verify_integrity.py | tee log_verify.txt

# Performance after recovery
echo ""
echo "Measuring performance after recovery..."
./performance_test.sh | tee log_performance_after.txt

echo ""
echo "✓ ALL TESTS COMPLETE"
echo ""
echo "Generated logs:"
ls -lh log_*.txt
echo ""
echo "Summary:"
echo "- Baseline:   log_status_baseline.txt, log_performance_baseline.txt"
echo "- Failure:   log_failure.txt"
echo "- During:    log_test_during.txt, log_performance_during.txt"
echo "- Recovery:  log_restore.txt, log_verify.txt, log_performance_after.txt"