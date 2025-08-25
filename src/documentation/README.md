# OWLS Archive Q4 - LocalStack Implementation

A four-quadrant operator and pipeline system for data analysis, designed with a **frozen control-plane** architecture to minimize AWS Config costs while maximizing data processing throughput.

## 🏗️ Architecture Overview

### Frozen Control-Plane Design

This implementation follows strict design principles to avoid AWS Config charges:

- **Deploy Once**: All AWS resources (buckets, queues, Lambda, IAM) are created once and never modified
- **Data-Plane Operations**: All runtime work uses S3 objects, SQS messages, and Lambda invocations
- **Prefix Organization**: Results are organized by prefixes (`run=YYYY-MM-DD-HHMMSS/`) instead of creating new resources
- **LocalStack Free Services**: Uses only S3, SQS, Lambda, and IAM (no Step Functions, DynamoDB, etc.)

### Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   S3 Archive    │    │   SQS Work       │    │  Lambda Q4      │
│   Bucket        │───▶│   Queue          │───▶│  Processor      │
│                 │    │                  │    │                 │
│ run=*/input/    │    │ Processing       │    │ Four-quadrant   │
│                 │    │ Messages         │    │ Analysis        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐             │
│  S3 Artifacts   │◀───│   SQS Done       │◀────────────┘
│  Bucket         │    │   Queue          │
│                 │    │                  │
│ run=*/output/   │    │ Completion       │
│ run=*/manifests/│    │ Notifications    │
└─────────────────┘    └──────────────────┘
```

## 🚀 Quick Start

### 1. Start LocalStack

```bash
# Start LocalStack with docker-compose
docker-compose up -d

# Verify it's running
curl http://localhost:4566/_localstack/health
```

### 2. Deploy Infrastructure (One-Time)

```bash
# Deploy all AWS resources (frozen control-plane)
./deploy.sh
```

This creates:
- 2 S3 buckets (archive, artifacts)
- 2 SQS queues (work, done)
- 1 Lambda function
- 1 IAM role with policies
- Event source mapping

### 3. Test the Pipeline

```bash
# Run end-to-end test (data-plane operations only)
./test_q4_pipeline.sh
```

## 📊 Q4 Processing Algorithm

The system implements a four-quadrant data decomposition:

1. **Learn Projectors**: Uses PCA to learn linear projectors from input data
2. **Quadrant Split**: Projects data and splits based on sign of projections
3. **Energy Analysis**: Computes energy distribution across quadrants
4. **Signal/Noise Separation**: Keeps Q1+Q4 as signal, discards Q2+Q3 as noise

### Input/Output Format

**Input**: CSV or Parquet files with numerical columns
**Output**:
- `Q_keep.csv`: Signal data (quadrants 1 & 4)
- `Q_discard.csv`: Noise data (quadrants 2 & 3)
- `Q_study.json`: Analysis metadata
- `er.json`: Energy split metrics
- `MANIFEST.json`: File mapping and provenance

## 🔄 Data-Plane Operations

All runtime operations are data-plane only (no new AWS resources):

### Upload Data
```bash
aws s3 cp mydata.csv s3://owls-q4-archive/run=2025-08-25-001/input/mydata.csv
```

### Trigger Processing
```bash
aws sqs send-message \
  --queue-url $WORK_QUEUE_URL \
  --message-body '{"input_key":"run=2025-08-25-001/input/mydata.csv","run_id":"2025-08-25-001"}'
```

### Check Results
```bash
aws s3 ls s3://owls-q4-artifacts/run=2025-08-25-001/ --recursive
```

### Monitor Completion
```bash
aws sqs receive-message --queue-url $DONE_QUEUE_URL
```

## 📁 File Organization

All files are organized by run prefixes to avoid resource conflicts:

```
owls-q4-archive/
├── run=2025-08-25-001/
│   └── input/
│       └── data1.csv
├── run=2025-08-25-002/
│   └── input/
│       └── data2.csv
└── ...

owls-q4-artifacts/
├── run=2025-08-25-001/
│   ├── Q_keep.csv
│   ├── Q_discard.csv
│   ├── Q_study.json
│   ├── er.json
│   └── MANIFEST.json
├── run=2025-08-25-002/
│   └── ...
└── ...
```

## 🛠️ Development

### Local Testing

```bash
# Install dependencies
pip install pandas numpy scikit-learn boto3

# Test Q4 algorithm locally
python -c "
import pandas as pd
import numpy as np
from lambda_function import learn_projectors_linear, four_quadrants, energy_split

# Create test data
data = np.random.randn(100, 4)
projectors, scaler = learn_projectors_linear(data)
q1, q2, q3, q4 = four_quadrants(data, projectors)
energy = energy_split(q1, q2, q3, q4)
print('Energy split:', energy)
"
```

### Modify Lambda Function

1. Edit `lambda_function.py`
2. Redeploy: `./deploy.sh`
3. Test: `./test_q4_pipeline.sh`

### Add New Data Sources

The system supports CSV and Parquet files. To add new formats:

1. Modify the file loading logic in `process_q4_data()`
2. Update the Lambda function
3. Redeploy

## 🔒 Cost Control Features

### AWS Config Compliance

- **No Resource Churn**: Infrastructure is deployed once and frozen
- **Prefix-Based Organization**: Uses S3 prefixes instead of new buckets
- **Reusable Compute**: Same Lambda function handles all processing
- **Static IAM**: Roles and policies never change after deployment

### LocalStack Free Tier

Uses only free LocalStack services:
- ✅ S3 (object storage)
- ✅ SQS (message queuing)  
- ✅ Lambda (compute)
- ✅ IAM (permissions)
- ❌ Step Functions (would require Pro)
- ❌ DynamoDB (not needed for this use case)

## 📈 Scaling Considerations

### Horizontal Scaling
- Increase Lambda concurrency for parallel processing
- Use SQS batch processing for higher throughput
- Partition data by prefixes for independent processing

### Vertical Scaling
- Increase Lambda memory/timeout for larger datasets
- Use Parquet format for better I/O performance
- Implement streaming for very large files

## 🐛 Troubleshooting

### Common Issues

**Lambda timeout**: Increase timeout in `infrastructure.tf`
```hcl
timeout = 900  # 15 minutes
```

**Memory errors**: Increase Lambda memory
```hcl
memory_size = 1024  # MB
```

**SQS visibility timeout**: Ensure it's longer than Lambda timeout

### Debugging

```bash
# Check Lambda logs
aws logs describe-log-groups
aws logs get-log-events --log-group-name /aws/lambda/owls-q4-processor

# Check queue status
aws sqs get-queue-attributes --queue-url $WORK_QUEUE_URL --attribute-names All

# Inspect S3 objects
aws s3 ls s3://owls-q4-archive/ --recursive
aws s3 ls s3://owls-q4-artifacts/ --recursive
```

## 📚 References

- [LocalStack Documentation](https://docs.localstack.cloud/)
- [AWS Lambda Python Runtime](https://docs.aws.amazon.com/lambda/latest/dg/python-programming-model.html)
- [Frozen Control-Plane Design Pattern](./research.readme.use)
- [Q4 Algorithm Specification](./.kiro/steering/)

## 🤝 Contributing

1. Follow the frozen control-plane design principles
2. All runtime operations must be data-plane only
3. Use prefixes for organization, never create new resources
4. Test with LocalStack before any AWS deployment
5. Maintain compatibility with free LocalStack services
