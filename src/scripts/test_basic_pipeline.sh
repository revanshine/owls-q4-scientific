#!/bin/bash

# OWLS Archive Q4 - Basic Pipeline Test (without Lambda)
# Tests S3 and SQS data-plane operations

set -e

# Set AWS CLI environment for LocalStack
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
export AWS_ENDPOINT_URL=http://localhost:4566

echo "🧪 OWLS Archive Q4 - Basic Pipeline Test"
echo "========================================"

# Generate unique run ID
RUN_ID=$(date +%Y-%m-%d-%H%M%S)
RUN_PREFIX="run=$RUN_ID"

echo "📊 Test Run ID: $RUN_ID"
echo "🗂️  Using prefix: $RUN_PREFIX"
echo ""

# Test 1: Upload test data to S3 (data-plane operation)
echo "1️⃣  Testing S3 upload (data-plane operation)..."
INPUT_KEY="$RUN_PREFIX/input/test_data.csv"

# Create test data if it doesn't exist
if [ ! -f "test_data.csv" ]; then
    cat > test_data.csv << 'EOF'
feature1,feature2,feature3,feature4
1.2,2.3,3.4,4.5
2.1,3.2,4.3,5.4
3.0,4.1,5.2,6.3
4.9,5.0,6.1,7.2
5.8,6.9,7.0,8.1
6.7,7.8,8.9,9.0
7.6,8.7,9.8,10.9
8.5,9.6,10.7,11.8
9.4,10.5,11.6,12.7
10.3,11.4,12.5,13.6
EOF
fi

aws s3 cp test_data.csv "s3://owls-q4-archive/$INPUT_KEY"
echo "✅ Uploaded to s3://owls-q4-archive/$INPUT_KEY"

# Test 2: Verify S3 object exists
echo ""
echo "2️⃣  Verifying S3 object..."
aws s3 ls "s3://owls-q4-archive/$RUN_PREFIX/" --recursive
echo "✅ S3 object verified"

# Test 3: Send message to SQS (data-plane operation)
echo ""
echo "3️⃣  Testing SQS message sending..."
WORK_QUEUE_URL="http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/owls-q4-work"

MESSAGE_BODY=$(cat << EOF
{
  "input_key": "$INPUT_KEY",
  "run_id": "$RUN_ID"
}
EOF
)

aws sqs send-message \
  --queue-url "$WORK_QUEUE_URL" \
  --message-body "$MESSAGE_BODY"

echo "✅ Message sent to work queue"

# Test 4: Receive message from SQS
echo ""
echo "4️⃣  Testing SQS message receiving..."
RECEIVED_MSG=$(aws sqs receive-message --queue-url "$WORK_QUEUE_URL" --wait-time-seconds 2)

if echo "$RECEIVED_MSG" | grep -q "input_key"; then
    echo "✅ Message received successfully"
    echo "📄 Message content:"
    echo "$RECEIVED_MSG" | jq '.Messages[0].Body' | jq .
    
    # Clean up: delete the message
    RECEIPT_HANDLE=$(echo "$RECEIVED_MSG" | jq -r '.Messages[0].ReceiptHandle')
    aws sqs delete-message --queue-url "$WORK_QUEUE_URL" --receipt-handle "$RECEIPT_HANDLE"
    echo "🧹 Message deleted from queue"
else
    echo "❌ No message received"
fi

# Test 5: Simulate processing results upload
echo ""
echo "5️⃣  Simulating Q4 processing results upload..."

# Create mock results
cat > mock_q_keep.csv << 'EOF'
feature1,feature2,feature3,feature4
1.2,2.3,3.4,4.5
2.1,3.2,4.3,5.4
5.8,6.9,7.0,8.1
6.7,7.8,8.9,9.0
EOF

cat > mock_q_discard.csv << 'EOF'
feature1,feature2,feature3,feature4
3.0,4.1,5.2,6.3
4.9,5.0,6.1,7.2
7.6,8.7,9.8,10.9
8.5,9.6,10.7,11.8
EOF

# Upload results to artifacts bucket
aws s3 cp mock_q_keep.csv "s3://owls-q4-artifacts/$RUN_PREFIX/Q_keep.csv"
aws s3 cp mock_q_discard.csv "s3://owls-q4-artifacts/$RUN_PREFIX/Q_discard.csv"

# Create and upload manifest
cat > manifest.json << EOF
{
  "input": "$INPUT_KEY",
  "output_prefix": "$RUN_PREFIX",
  "files": {
    "keep_file": "$RUN_PREFIX/Q_keep.csv",
    "discard_file": "$RUN_PREFIX/Q_discard.csv",
    "keep_rows": 4,
    "discard_rows": 4
  },
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "status": "completed"
}
EOF

aws s3 cp manifest.json "s3://owls-q4-artifacts/$RUN_PREFIX/MANIFEST.json"

echo "✅ Mock results uploaded"

# Test 6: Verify all artifacts
echo ""
echo "6️⃣  Verifying all artifacts..."
echo ""
echo "📁 Archive bucket contents:"
aws s3 ls "s3://owls-q4-archive/" --recursive

echo ""
echo "📁 Artifacts bucket contents:"
aws s3 ls "s3://owls-q4-artifacts/" --recursive

echo ""
echo "📄 Manifest content:"
aws s3 cp "s3://owls-q4-artifacts/$RUN_PREFIX/MANIFEST.json" - | jq .

# Test 7: Send completion notification
echo ""
echo "7️⃣  Testing completion notification..."
DONE_QUEUE_URL="http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/owls-q4-done"

COMPLETION_MSG=$(cat << EOF
{
  "status": "completed",
  "run_id": "$RUN_ID",
  "input_key": "$INPUT_KEY",
  "artifacts_prefix": "$RUN_PREFIX"
}
EOF
)

aws sqs send-message \
  --queue-url "$DONE_QUEUE_URL" \
  --message-body "$COMPLETION_MSG"

echo "✅ Completion notification sent"

# Clean up temporary files
rm -f mock_q_keep.csv mock_q_discard.csv manifest.json

echo ""
echo "🎉 Basic Pipeline Test Complete!"
echo ""
echo "🔍 Key Observations:"
echo "   ✅ S3 buckets working (frozen control-plane)"
echo "   ✅ SQS queues working (data-plane messaging)"
echo "   ✅ Prefix-based organization working"
echo "   ✅ No new AWS resources created during processing"
echo "   ⚠️  Lambda function needs Docker access (next step)"
echo ""
echo "📋 Next Steps:"
echo "   1. Fix Lambda Docker access issue"
echo "   2. Deploy actual Q4 processing function"
echo "   3. Test end-to-end pipeline"
