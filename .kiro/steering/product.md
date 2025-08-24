# Product Overview

OWLS Archive Q4 is a four-quadrant operator and pipeline system for data analysis. The system performs linear projection-based data decomposition, splitting input data into "keep" and "discard" quadrants based on learned projectors.

## Core Functionality

- Learns linear projectors from input data (supervised or unsupervised)
- Applies four-quadrant decomposition to separate signal from noise
- Outputs structured results including energy split metrics and manifests
- Designed for batch processing of CSV/Parquet data files

## Target Infrastructure

The system is designed to be deployed on AWS infrastructure using:

- S3 for data storage
- SQS for message queuing
- Lambda for serverless execution
- Step Functions (SFN) for workflow orchestration

## Future Extensions

- FITS file loader support
- Time-series data flattening
- Kolmogorov-Smirnov and correlation gates for enhanced testing
