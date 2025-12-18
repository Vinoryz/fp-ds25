#!/bin/bash
echo "  TEST OPERATIONS DURING FAILURE"
echo ""

# Test 1: WRITE
echo "=== TEST 1: WRITE (Upload) ==="
echo "Test data during failure" > /tmp/test_write.txt

START=$(date +%s.%N)
mc cp /tmp/test_write.txt myminio/testbucket/test_during_failure.txt
WRITE_STATUS=$? 
END=$(date +%s.%N)

WRITE_TIME=$(echo "$END - $START" | bc)

if [ $WRITE_STATUS -eq 0 ]; then
    echo "✓ WRITE SUCCESS"
    echo "  Time: ${WRITE_TIME}s"
else
    echo "✗ WRITE FAILED"
fi

echo ""

# Test 2: READ
echo "=== TEST 2: READ (Download) ==="
echo "Testing file:  testfile_1.dat"

START=$(date +%s.%N)
mc cp myminio/testbucket/testfile_1.dat /tmp/test_read.dat 2>&1
READ_STATUS=$? 
END=$(date +%s.%N)

READ_TIME=$(echo "$END - $START" | bc)

if [ $READ_STATUS -eq 0 ]; then
    echo "✓ READ SUCCESS"
    echo "  Time: ${READ_TIME}s"
else
    echo "✗ READ FAILED"
fi

echo ""

# Test 3: LIST
echo "=== TEST 3: LIST (Bucket Operations) ==="

START=$(date +%s.%N)
mc ls myminio/testbucket/ > /dev/null
LIST_STATUS=$?
END=$(date +%s.%N)

LIST_TIME=$(echo "$END - $START" | bc)

if [ $LIST_STATUS -eq 0 ]; then
    FILE_COUNT=$(mc ls myminio/testbucket/ | wc -l)
    echo "✓ LIST SUCCESS"
    echo "  Files: $FILE_COUNT"
    echo "  Time: ${LIST_TIME}s"
else
    echo "✗ LIST FAILED"
fi

echo ""
echo "SUMMARY"
echo "Write: $([ $WRITE_STATUS -eq 0 ] && echo 'OK' || echo 'FAIL') (${WRITE_TIME}s)"
echo "Read:   $([ $READ_STATUS -eq 0 ] && echo 'OK' || echo 'FAIL') (${READ_TIME}s)"
echo "List:  $([ $LIST_STATUS -eq 0 ] && echo 'OK' || echo 'FAIL') (${LIST_TIME}s)"
echo ""

# Analisis Quorum
echo "=== ANALISIS QUORUM ==="
ONLINE_DRIVES=$(mc admin info myminio | grep "drives online" | awk '{print $1}')
echo "Drives online: $ONLINE_DRIVES/6"
echo "Write quorum minimum: 4 drives (N/2 + 1)"
echo "Read quorum minimum: 4 drives (EC:2)"

if [ "$ONLINE_DRIVES" -ge 4 ]; then
    echo "✓ Quorum TERPENUHI ($ONLINE_DRIVES >= 4)"
else
    echo "✗ Quorum TIDAK TERPENUHI ($ONLINE_DRIVES < 4)"
fi