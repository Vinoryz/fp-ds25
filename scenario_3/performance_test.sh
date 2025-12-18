#!/bin/bash
echo "=========================================="
echo "  PERFORMANCE MEASUREMENT"
echo "=========================================="
echo ""

# Create 50MB test file
echo "Creating 50MB test file..."
dd if=/dev/urandom of=/tmp/perf_test.dat bs=1M count=50 2>/dev/null
echo "✓ File created"
echo ""

# Upload test
echo "=== UPLOAD TEST ==="
START=$(date +%s.%N)
mc cp /tmp/perf_test.dat myminio/testbucket/perf_test.dat
END=$(date +%s.%N)

UPLOAD_TIME=$(echo "$END - $START" | bc)
UPLOAD_SPEED=$(echo "scale=2; 50 / $UPLOAD_TIME" | bc)

echo "Upload time: ${UPLOAD_TIME}s"
echo "Upload speed: ${UPLOAD_SPEED} MB/s"
echo ""

# Download test
echo "=== DOWNLOAD TEST ==="
rm -f /tmp/perf_download.dat

START=$(date +%s.%N)
mc cp myminio/testbucket/perf_test.dat /tmp/perf_download.dat
END=$(date +%s.%N)

DOWNLOAD_TIME=$(echo "$END - $START" | bc)
DOWNLOAD_SPEED=$(echo "scale=2; 50 / $DOWNLOAD_TIME" | bc)

echo "Download time: ${DOWNLOAD_TIME}s"
echo "Download speed: ${DOWNLOAD_SPEED} MB/s"
echo ""

# Integrity check
ORIG_MD5=$(md5sum /tmp/perf_test.dat | awk '{print $1}')
DOWN_MD5=$(md5sum /tmp/perf_download.dat | awk '{print $1}')

if [ "$ORIG_MD5" == "$DOWN_MD5" ]; then
    echo "✓ Integrity check PASSED"
else
    echo "✗ Integrity check FAILED"
fi

echo ""
echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo "Upload:    ${UPLOAD_SPEED} MB/s (${UPLOAD_TIME}s)"
echo "Download: ${DOWNLOAD_SPEED} MB/s (${DOWNLOAD_TIME}s)"