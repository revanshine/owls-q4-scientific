#!/bin/bash

# OWLS Archive Q4 - LocalStack Deployment
# Frozen control-plane design: deploy once, use data-plane operations
# AWS Config compliant: minimal recording to avoid charges

set -e

echo "🦉 OWLS Archive Q4 - LocalStack Deployment"
echo "=========================================="
echo "🔒 Frozen Control-Plane Design with AWS Config Compliance"
echo ""

# Check if LocalStack is running
if ! curl -s http://localhost:4566/_localstack/health > /dev/null; then
    echo "❌ LocalStack not running. Start with: docker-compose up -d"
    exit 1
fi

echo "✅ LocalStack is running"

# Set AWS CLI environment for LocalStack
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
export AWS_ENDPOINT_URL=http://localhost:4566

# Create Lambda deployment package
echo "📦 Creating Lambda deployment package..."
mkdir -p lambda_package
cp lambda_function.py lambda_package/

# Create a minimal requirements.txt for Lambda
cat > lambda_package/requirements.txt << EOF
pandas
numpy
scikit-learn
EOF

# Create the zip file (LocalStack doesn't need actual dependencies for testing)
cd lambda_package
zip -r ../q4_processor.zip .
cd ..
rm -rf lambda_package

echo "✅ Lambda package created"

# Deploy infrastructure with Terraform
echo "🏗️  Deploying infrastructure (control-plane - do this once)..."
echo "🔧 Config Mode: $(grep 'config_mode' terraform.tfvars | cut -d'"' -f2)"
terraform init
terraform plan
terraform apply -auto-approve

echo "✅ Infrastructure deployed"

# Get outputs for testing
ARCHIVE_BUCKET=$(terraform output -raw archive_bucket)
ARTIFACTS_BUCKET=$(terraform output -raw artifacts_bucket)
WORK_QUEUE_URL=$(terraform output -raw work_queue_url)
DONE_QUEUE_URL=$(terraform output -raw done_queue_url)

# Show Config compliance info
echo ""
echo "🛡️  AWS Config Compliance Status"
echo "================================="
terraform output config_cost_optimization

echo ""
echo "🎯 Deployment Complete - Ready for Data-Plane Operations"
echo "======================================================="
echo "Archive Bucket: $ARCHIVE_BUCKET"
echo "Artifacts Bucket: $ARTIFACTS_BUCKET"
echo "Work Queue: $WORK_QUEUE_URL"
echo "Done Queue: $DONE_QUEUE_URL"
echo ""
echo "📋 Usage Examples (Data-Plane Operations Only):"
echo ""
echo "1. Upload test data:"
echo "   aws s3 cp test_data.csv s3://$ARCHIVE_BUCKET/run=2025-08-25/input/test_data.csv"
echo ""
echo "2. Send processing message:"
echo "   aws sqs send-message --queue-url $WORK_QUEUE_URL --message-body '{\"input_key\":\"run=2025-08-25/input/test_data.csv\",\"run_id\":\"2025-08-25-001\"}'"
echo ""
echo "3. Check results:"
echo "   aws s3 ls s3://$ARTIFACTS_BUCKET/run=2025-08-25-001/ --recursive"
echo ""
echo "4. Monitor completion:"
echo "   aws sqs receive-message --queue-url $DONE_QUEUE_URL"
echo ""
echo "🔒 Control-Plane Frozen: No new resources will be created during processing"
echo "📊 All operations use prefixes and existing infrastructure"
echo "💰 AWS Config: Only recording control-plane resources (minimal charges)"

# Create sample test data
echo ""
echo "📝 Creating sample test data..."
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

echo "✅ Sample data created: test_data.csv"
echo ""
echo "🚀 Ready to test! Run the usage examples above."
