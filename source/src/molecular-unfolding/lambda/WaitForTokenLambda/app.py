import boto3
import json
import logging

s3 = boto3.client('s3')
step_func = boto3.client('stepfunctions')
s3_prefix = None
s3_bucket = None

log = logging.getLogger()
log.setLevel('INFO')

def string_to_s3(content, bucket, key):
    log.info(f"write s3://{bucket}/{key}, content={content}")
    s3.put_object(
        Body=content.encode("utf-8"),
        Bucket=bucket,
        Key=key
    )


def read_user_input(execution_id, bucket, s3_prefix):
    key = f"{s3_prefix}/executions/{execution_id}/user_input.json"
    log.info(f"read s3://{bucket}/{key}")
    obj = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(obj['Body'].read())


def read_as_json(bucket, key):
    log.info(f"read s3://{bucket}/{key}")
    obj = s3.get_object(Bucket=bucket, Key=key)
    json_ = json.loads(obj['Body'].read())
    log.info(f"return: {json_}")
    return json_


def save_token_for_task_id(execution_id, qc_task_id, task_token, batch_job_id, submit_result, s3_bucket):
    key = f"{s3_prefix}/qc_task_token/{qc_task_id}.json"
    string_to_s3(json.dumps({
        "execution_id": execution_id,
        "qc_task_id": qc_task_id,
        "task_token": task_token,
        "batch_job_id": batch_job_id,
        "submit_result": submit_result
    }), s3_bucket, key)
    log.info(f"saved s3://{s3_bucket}/{key}")


def read_sumbit_result(execution_id, batch_job_id):
    log.info("read_sumbit_result() ")
    key = f"{s3_prefix}/executions/{execution_id}/qa_batch_jobs/{batch_job_id}.json"
    return read_as_json(s3_bucket, key)


def handler(event, context):
    # log.info(f"event={event}")

    global s3_bucket
    global s3_prefix

    s3_bucket = event['s3_bucket']
    s3_prefix = event['s3_prefix']

    task_token = event['task_token']
    execution_id = event['execution_id']
    batch_job_id = event['batch_job_id']

    batch_result = read_sumbit_result(execution_id, batch_job_id)

    qc_task_id = batch_result['qc_task_id']
    submit_result = batch_result['submit_result']

    log.info(f"qc_task_id={qc_task_id}")
    save_token_for_task_id(execution_id, qc_task_id,
                           task_token, batch_job_id, submit_result, s3_bucket)
