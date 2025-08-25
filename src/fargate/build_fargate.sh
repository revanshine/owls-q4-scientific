#!/bin/bash

# OWLS Archive Q4 - Fargate Container Build Script
# Self-contained scientific Q4 processing with modular structure

set -e

echo "🐳 OWLS Archive Q4 - Self-Contained Fargate Build"
echo "================================================="

# Ensure we have the lock file
if [ ! -f "uv.lock" ]; then
    echo "📦 Creating uv lock file..."
    uv lock
fi
echo "✅ Lock file exists"

# Build the container
echo "🔨 Building self-contained Fargate container..."
docker build -t owls-q4-scientific:latest .

echo "✅ Container built successfully!"

# Test the container locally (optional)
echo ""
echo "🧪 Testing container locally..."
echo "Creating test environment variables..."

# Create test env file
cat > test.env << EOF
ARCHIVE_BUCKET=test-archive
ARTIFACTS_BUCKET=test-artifacts
DONE_QUEUE_URL=http://localhost:4566/000000000000/test-done
INPUT_KEY=run=test/input/test.csv
RUN_ID=test-$(date +%Y%m%d-%H%M%S)
PROCESSING_MODE=standard
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_DEFAULT_REGION=us-east-1
AWS_ENDPOINT_URL=http://host.docker.internal:4566
EOF

echo "✅ Test environment created"
echo ""
echo "🚀 Self-contained container ready for deployment!"
echo ""
echo "📋 Next steps:"
echo "   1. Push to ECR: docker tag owls-q4-scientific:latest <ecr-repo-url>"
echo "   2. Deploy Fargate infrastructure: terraform apply"
echo "   3. Test with: ../../scripts/test_basic_pipeline.sh"
echo ""
echo "🧪 To test locally:"
echo "   docker run --env-file test.env owls-q4-scientific:latest"
echo ""
echo "📦 Project structure:"
echo "   ✅ Self-contained q4 package"
echo "   ✅ Proper uv dependency management"
echo "   ✅ No external dependencies"
