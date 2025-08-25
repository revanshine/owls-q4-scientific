#!/usr/bin/env python3
"""
OWLS Archive Q4 - Fargate Processor
Scientific Q4 processing using the actual scientific code from owls-archive-q4-qstudy
Runs as ECS Fargate task with proper dependency management
"""

import json
import os
import sys
import boto3
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np

# Import the scientific Q4 code (now local modules)
from q4.operator import learn_projectors_linear, four_quadrants, energy_split
from q4.svd_ops import SVDModel, center_l2, fit_svd, project
from q4.qstudy_map import compute_qstudy_vectors, embed_reduce_heatmap

# Initialize AWS clients
s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')

def get_env_var(name, required=True):
    """Get environment variable with error handling"""
    value = os.environ.get(name)
    if required and not value:
        raise ValueError(f"Required environment variable {name} not set")
    return value

def process_q4_scientific_fargate(input_key, run_prefix, processing_mode="standard"):
    """
    Process data using scientific Q4 implementation in Fargate
    Full access to all scientific dependencies and capabilities
    """
    
    archive_bucket = get_env_var('ARCHIVE_BUCKET')
    artifacts_bucket = get_env_var('ARTIFACTS_BUCKET')
    
    try:
        print(f"🔬 Starting scientific Q4 Fargate processing: {input_key}")
        print(f"📊 Processing mode: {processing_mode}")
        
        # Download and parse input data
        print("📥 Downloading input data...")
        response = s3_client.get_object(Bucket=archive_bucket, Key=input_key)
        
        if input_key.endswith('.csv'):
            df = pd.read_csv(response['Body'])
        elif input_key.endswith('.parquet'):
            df = pd.read_parquet(response['Body'])
        else:
            raise ValueError(f"Unsupported file type: {input_key}")
        
        # Convert to numpy array (scientific code expects this)
        X = df.to_numpy(dtype=float)
        print(f"✅ Loaded data shape: {X.shape}")
        
        # Step 1: Core Q4 Analysis (using scientific implementation)
        print("🧮 Performing Q4 analysis...")
        Ps, Pv = learn_projectors_linear(X, labels=None, r=1)
        q_result = four_quadrants(X, Ps, Pv)
        energy_ratio = energy_split(X, Ps, Pv)
        
        print(f"✅ Q4 analysis complete - Energy ratio: {energy_ratio:.4f}")
        
        # Step 2: Enhanced SVD Analysis
        svd_analysis = {}
        Z = None
        
        if processing_mode in ["enhanced", "full"]:
            print("🔍 Performing enhanced SVD analysis...")
            
            # Use scientific SVD operations with full capabilities
            Vn, mu = center_l2(X)
            k = min(50, X.shape[1], X.shape[0])
            svd_model = fit_svd(Vn, k=k, seed=42)
            svd_model.mu = mu
            
            Z = project(X, svd_model)
            
            # Save SVD model for potential reuse
            model_data = svd_model.to_dict()
            model_key = f"{run_prefix}/svd_model.json"
            s3_client.put_object(
                Bucket=artifacts_bucket,
                Key=model_key,
                Body=json.dumps(model_data, indent=2)
            )
            
            svd_analysis = {
                "model_file": model_key,
                "projection_shape": Z.shape,
                "explained_variance_ratio": (svd_model.explained_variance / svd_model.explained_variance.sum()).tolist()[:10],
                "total_explained_variance": float(svd_model.explained_variance.sum())
            }
            
            print(f"✅ SVD analysis complete - Projection shape: {Z.shape}")
        
        # Step 3: Q_study Analysis with Visualization
        qstudy_analysis = {}
        
        if processing_mode == "full" and Z is not None:
            print("📈 Performing Q_study analysis with visualization...")
            
            # Compute Q_study features
            qstudy_features = compute_qstudy_vectors(Z)
            
            # Create visualization artifacts (only possible in Fargate with full deps)
            try:
                # Create temporary directory for plots
                plot_dir = Path("/tmp/qstudy_plots")
                plot_dir.mkdir(exist_ok=True)
                
                # Create Q_study DataFrame for visualization
                qstudy_df = pd.DataFrame([qstudy_features])
                qstudy_df.insert(0, "win_id", 0)
                
                # Generate embeddings and heatmaps
                artifacts = embed_reduce_heatmap(qstudy_df, plot_dir, reducer="pca", bins=40)
                
                # Upload visualization artifacts to S3
                viz_artifacts = {}
                for artifact_name, local_path in artifacts.items():
                    if Path(local_path).exists():
                        s3_key = f"{run_prefix}/visualizations/{Path(local_path).name}"
                        s3_client.upload_file(local_path, artifacts_bucket, s3_key)
                        viz_artifacts[artifact_name] = s3_key
                        print(f"📊 Uploaded {artifact_name}: {s3_key}")
                
                qstudy_analysis = {
                    "features": qstudy_features,
                    "visualizations": viz_artifacts
                }
                
            except Exception as viz_error:
                print(f"⚠️ Visualization failed (continuing without): {viz_error}")
                qstudy_analysis = {"features": qstudy_features}
            
            print("✅ Q_study analysis complete")
        
        # Prepare outputs using scientific format
        timestamp = datetime.utcnow().isoformat()
        results = {}
        
        # Save Q4 results
        if hasattr(q_result, 'Q_keep') and q_result.Q_keep.size > 0:
            keep_df = pd.DataFrame(q_result.Q_keep, columns=df.columns)
            keep_key = f"{run_prefix}/Q_keep.csv"
            keep_csv = keep_df.to_csv(index=False)
            s3_client.put_object(Bucket=artifacts_bucket, Key=keep_key, Body=keep_csv)
            results['keep_file'] = keep_key
            results['keep_rows'] = int(q_result.Q_keep.shape[0])
            print(f"💾 Saved Q_keep: {results['keep_rows']} rows")
        
        if hasattr(q_result, 'Q_discard') and q_result.Q_discard.size > 0:
            discard_df = pd.DataFrame(q_result.Q_discard, columns=df.columns)
            discard_key = f"{run_prefix}/Q_discard.csv"
            discard_csv = discard_df.to_csv(index=False)
            s3_client.put_object(Bucket=artifacts_bucket, Key=discard_key, Body=discard_csv)
            results['discard_file'] = discard_key
            results['discard_rows'] = int(q_result.Q_discard.shape[0])
            print(f"💾 Saved Q_discard: {results['discard_rows']} rows")
        
        # Enhanced study metadata
        study_data = {
            "timestamp": timestamp,
            "input_file": input_key,
            "algorithm": "scientific_q4_fargate",
            "processing_mode": processing_mode,
            "runtime_environment": "fargate",
            "data_shape": X.shape,
            "q4_analysis": {
                "projector_shapes": {"Ps": Ps.shape, "Pv": Pv.shape},
                "q_study": q_result.Q_study,
                "energy_split": energy_ratio
            }
        }
        
        if svd_analysis:
            study_data["svd_analysis"] = svd_analysis
        if qstudy_analysis:
            study_data["qstudy_analysis"] = qstudy_analysis
        
        study_key = f"{run_prefix}/Q_study.json"
        s3_client.put_object(
            Bucket=artifacts_bucket,
            Key=study_key,
            Body=json.dumps(study_data, indent=2)
        )
        results['study_file'] = study_key
        
        # Energy report
        energy_metrics = {
            "energy_split": energy_ratio,
            "total_rows": int(X.shape[0]),
            "dimensions": int(X.shape[1]),
            "keep_ratio": results.get('keep_rows', 0) / X.shape[0],
            "discard_ratio": results.get('discard_rows', 0) / X.shape[0],
            "algorithm": "scientific_q4_fargate",
            "processing_mode": processing_mode
        }
        
        er_key = f"{run_prefix}/er.json"
        s3_client.put_object(
            Bucket=artifacts_bucket,
            Key=er_key,
            Body=json.dumps(energy_metrics, indent=2)
        )
        results['energy_report'] = er_key
        
        # Comprehensive manifest
        manifest = {
            "input": input_key,
            "output_prefix": run_prefix,
            "files": results,
            "timestamp": timestamp,
            "status": "completed",
            "algorithm": "scientific_q4_fargate",
            "processing_mode": processing_mode,
            "runtime_environment": "fargate",
            "enhancements": {
                "svd_analysis": bool(svd_analysis),
                "qstudy_analysis": bool(qstudy_analysis),
                "visualizations": bool(qstudy_analysis.get('visualizations', {}))
            }
        }
        
        manifest_key = f"{run_prefix}/MANIFEST.json"
        s3_client.put_object(
            Bucket=artifacts_bucket,
            Key=manifest_key,
            Body=json.dumps(manifest, indent=2)
        )
        
        print(f"✅ Scientific Q4 Fargate processing completed successfully")
        print(f"📊 Results: {len(results)} files generated")
        return manifest
        
    except Exception as e:
        print(f"❌ Error in scientific Q4 Fargate processing: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Create error manifest
        error_manifest = {
            "input": input_key,
            "output_prefix": run_prefix,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error": str(e),
            "algorithm": "scientific_q4_fargate",
            "processing_mode": processing_mode,
            "runtime_environment": "fargate"
        }
        
        error_key = f"{run_prefix}/ERROR.json"
        s3_client.put_object(
            Bucket=artifacts_bucket,
            Key=error_key,
            Body=json.dumps(error_manifest, indent=2)
        )
        
        raise e

def send_completion_notification(manifest, run_id, input_key, processing_mode):
    """Send completion notification to SQS done queue"""
    try:
        done_queue_url = get_env_var('DONE_QUEUE_URL')
        
        completion_message = {
            "status": "completed",
            "run_id": run_id,
            "input_key": input_key,
            "processing_mode": processing_mode,
            "runtime_environment": "fargate",
            "manifest": manifest
        }
        
        sqs_client.send_message(
            QueueUrl=done_queue_url,
            MessageBody=json.dumps(completion_message)
        )
        
        print("✅ Completion notification sent to SQS")
        
    except Exception as e:
        print(f"⚠️ Failed to send completion notification: {e}")

def main():
    """Main Fargate processor entry point"""
    
    try:
        print("🚀 OWLS Archive Q4 - Fargate Scientific Processor")
        print("=" * 50)
        
        # Get processing parameters from environment variables
        input_key = get_env_var('INPUT_KEY')
        run_id = get_env_var('RUN_ID')
        processing_mode = get_env_var('PROCESSING_MODE', required=False) or 'standard'
        
        run_prefix = f"run={run_id}"
        
        print(f"📋 Processing Parameters:")
        print(f"   Input: {input_key}")
        print(f"   Run ID: {run_id}")
        print(f"   Mode: {processing_mode}")
        print(f"   Prefix: {run_prefix}")
        print()
        
        # Process the data
        manifest = process_q4_scientific_fargate(input_key, run_prefix, processing_mode)
        
        # Send completion notification
        send_completion_notification(manifest, run_id, input_key, processing_mode)
        
        print("🎉 Fargate processing completed successfully!")
        sys.exit(0)
        
    except Exception as e:
        print(f"💥 Fargate processor failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
