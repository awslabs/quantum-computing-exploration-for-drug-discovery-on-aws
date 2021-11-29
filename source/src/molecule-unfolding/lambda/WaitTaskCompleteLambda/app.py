import boto3
import os
from collections import defaultdict
import json

s3 = boto3.client('s3')
s3_prefix = "molecule-unfolding"
step_func = boto3.client('stepfunctions')


def string_to_s3(content, bucket, key):
    s3.put_object(
        Body=content.encode("utf-8"),
        Bucket=bucket,
        Key=key
    )


def read_user_input(execution_id, bucket, s3_prefix):
    key = f"{s3_prefix}/executions/{execution_id}/user_input.json"
    obj = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(obj['Body'].read())


def read_as_json(bucket, key):
    obj = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(obj['Body'].read())


def get_qc_task_id(batch_job_id, s3_bucket):
    key = f"f{s3_prefix}/batch_job_and_qc_task_map/{batch_job_id}.json"
    return read_as_json(s3_bucket, key)['qc_task_id']


def save_token_for_task_id(execution_id, qc_task_id, batch_job_id, task_token, s3_bucket):
    key = f"f{s3_prefix}/qc_task_token/{qc_task_id}.json"
    string_to_s3(json.dumps({
        "execution_id": execution_id,
        "qc_task_id": qc_task_id,
        "batch_job_id": batch_job_id,
        "task_token": task_token,
    }), s3_bucket, key)


def handler(event, context):
    print(f"event={event}")
    s3_bucket = event['s3_bucket']
    aws_region = os.environ['AWS_REGION']
    task_token = event['task_token']
    execution_id = event['execution_id']

    batch_job_id = event['batch_job_id']
    qc_task_id = get_qc_task_id(batch_job_id, s3_bucket)
    save_token_for_task_id(execution_id, qc_task_id, batch_job_id, task_token, s3_bucket)

    # "execution_id": sfn.JsonPath.stringAt("$.execution_id"),
    # "batch_job_id": sfn.JsonPath.stringAt("$.QCBatchJobIterator.JobId"),
    # "task_token": sfn.JsonPath.taskToken,
    # "ItemIndex": sfn.JsonPath.stringAt("$.ItemIndex"),
    
    step_func.send_task_success(
        taskToken=task_token,
        output={
            'status': 'success',
            'batch_job_id': batch_job_id,
            'qc_task_id': qc_task_id,
            'execution_id': execution_id
        }
    )
