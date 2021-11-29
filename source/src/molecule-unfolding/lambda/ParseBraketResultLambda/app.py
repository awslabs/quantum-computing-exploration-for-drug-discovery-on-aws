import boto3
import os
from collections import defaultdict
import json
import datetime

s3 = boto3.client('s3')
s3_prefix = "molecule-unfolding"


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


def handler(event, context):
    print(f"event={event}")
    aws_region = os.environ['AWS_REGION']
   