"""
OWLS Archive Q4 - Lambda Orchestrator
Launches Fargate tasks for scientific Q4 processing
Maintains frozen control-plane design by reusing existing task definitions
"""

import json
import os
import boto3
from datetime import datetime

# Initialize AWS clients
ecs_client = boto3.client('ecs')
sqs_client = boto3.client('sqs')

# Environment variables (set once in infrastructure)
CLUSTER_NAME = os.environ['CLUSTER_NAME']
TASK_DEFINITION_ARN = os.environ['TASK_DEFINITION_ARN']
SUBNET_IDS = os.environ.get('SUBNET_IDS', '').split(',')
SECURITY_GROUP_IDS = os.environ.get('SECURITY_GROUP_IDS', '').split(',')

def launch_fargate_task(input_key, run_id, processing_mode="standard"):
    """
    Launch Fargate task for scientific Q4 processing
    Uses existing task definition with runtime environment variables (data-plane)
    """
    
    try:
        print(f"🚀 Launching Fargate task for: {input_key}")
        
        # Prepare task overrides (data-plane parameters)
        container_overrides = [
            {
                'name': 'q4-processor',
                'environment': [
                    {'name': 'INPUT_KEY', 'value': input_key},
                    {'name': 'RUN_ID', 'value': run_id},
                    {'name': 'PROCESSING_MODE', 'value': processing_mode}
                ]
            }
        ]
        
        # Network configuration for Fargate
        network_configuration = {
            'awsvpcConfiguration': {
                'subnets': SUBNET_IDS,
                'securityGroups': SECURITY_GROUP_IDS,
                'assignPublicIp': 'ENABLED'  # For LocalStack, may need internet access
            }
        }
        
        # Launch the task (data-plane operation - no new resources created)
        response = ecs_client.run_task(
            cluster=CLUSTER_NAME,
            taskDefinition=TASK_DEFINITION_ARN,
            launchType='FARGATE',
            networkConfiguration=network_configuration,
            overrides={
                'containerOverrides': container_overrides
            },
            tags=[
                {'key': 'Project', 'value': 'owls-q4'},
                {'key': 'RunId', 'value': run_id},
                {'key': 'ProcessingMode', 'value': processing_mode},
                {'key': 'InputKey', 'value': input_key}
            ]
        )
        
        task_arn = response['tasks'][0]['taskArn']
        print(f"✅ Fargate task launched: {task_arn}")
        
        return {
            'task_arn': task_arn,
            'cluster': CLUSTER_NAME,
            'run_id': run_id,
            'input_key': input_key,
            'processing_mode': processing_mode,
            'launch_time': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Failed to launch Fargate task: {str(e)}")
        raise e

def lambda_handler(event, context):
    """
    Lambda orchestrator handler
    Receives SQS messages and launches appropriate Fargate tasks
    """
    
    try:
        print(f"📨 Received orchestration event: {json.dumps(event)}")
        
        launched_tasks = []
        
        # Process SQS messages
        for record in event['Records']:
            message_body = json.loads(record['body'])
            print(f"🔍 Processing orchestration message: {message_body}")
            
            # Extract processing parameters
            input_key = message_body['input_key']
            run_id = message_body.get('run_id', datetime.utcnow().strftime('%Y-%m-%d-%H%M%S'))
            processing_mode = message_body.get('processing_mode', 'standard')
            
            # Determine processing strategy based on mode
            if processing_mode in ['enhanced', 'full']:
                # Use Fargate for heavy scientific processing
                print(f"🧬 Launching Fargate for scientific processing: {processing_mode}")
                task_info = launch_fargate_task(input_key, run_id, processing_mode)
                launched_tasks.append(task_info)
                
            else:
                # For simple processing, could still use Lambda (not implemented here)
                print(f"⚡ Standard processing mode - would use simple Lambda")
                # Could launch a simpler Lambda function here
                # For now, we'll use Fargate for all processing
                task_info = launch_fargate_task(input_key, run_id, processing_mode)
                launched_tasks.append(task_info)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Orchestrated {len(launched_tasks)} Fargate tasks',
                'launched_tasks': launched_tasks,
                'orchestrator': 'lambda_to_fargate'
            })
        }
        
    except Exception as e:
        print(f"💥 Orchestration error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'orchestrator': 'lambda_to_fargate'
            })
        }
