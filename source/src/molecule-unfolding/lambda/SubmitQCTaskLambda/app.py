import boto3
import os
import json
from process import submit_qc_task

s3 = boto3.client('s3')
s3_prefix = "molecule-unfolding"
step_func = boto3.client('stepfunctions')


def string_to_s3(content, bucket, key):
    print(f"write s3://{bucket}/{key}, content={content}")
    s3.put_object(
        Body=content.encode("utf-8"),
        Bucket=bucket,
        Key=key
    )


def read_user_input(execution_id, bucket, s3_prefix):
    key = f"{s3_prefix}/executions/{execution_id}/user_input.json"
    print(f"read s3://{bucket}/{key}")
    obj = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(obj['Body'].read())


def read_as_json(bucket, key):
    print(f"read s3://{bucket}/{key}")
    obj = s3.get_object(Bucket=bucket, Key=key)
    json_ = json.loads(obj['Body'].read())
    print(f"return: {json_}")
    return json_


def save_token_for_task_id(execution_id, qc_task_id, task_token, ItemValue, submit_res, s3_bucket):
    key = f"{s3_prefix}/qc_task_token/{qc_task_id}.json"
    string_to_s3(json.dumps({
        "execution_id": execution_id,
        "qc_task_id": qc_task_id,
        "task_token": task_token,
        "ItemValue": ItemValue,
        "submit_res": submit_res
    }), s3_bucket, key)
    print(f"saved s3://{s3_bucket}/{key}")


def handler(event, context):
    print(f"event={event}")
    s3_bucket = event['s3_bucket']
    aws_region = os.environ['AWS_REGION']
    task_token = event['task_token']
    execution_id = event['execution_id']
    ItemValue = event['ItemValue']

    device_arn = ItemValue['device_arn']
    model_param =ItemValue['model_param']

    submit_res = submit_qc_task(s3, execution_id, device_arn,
                                model_param, s3_bucket, s3_prefix)
    # {"task_id": task_id, "model_name": model_name,  "mode_file_name": mode_file_name}
    qc_task_id = submit_res['task_id']

    print(f"qc_task_id={qc_task_id}")
    save_token_for_task_id(execution_id, qc_task_id,
                           task_token, ItemValue, submit_res, s3_bucket)

