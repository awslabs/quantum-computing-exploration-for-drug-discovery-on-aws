import argparse
import logging
import boto3
import time
import datetime
import pickle
import json
from utility.AnnealerOptimizer import Annealer


logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.INFO)

DEFAULT_AWS_REGION = 'us-east-1'


def download_file(bucket, key, dir="./"):
    file_name = dir + key.split("/")[-1]

    with open(file_name, 'wb') as f:
        s3.download_fileobj(bucket, key, f)
    logging.info("download_file: {} -> {}".format(key, file_name))

    return file_name


def string_to_s3(content, bucket, key):
    s3.put_object(
        Body=content.encode("utf-8"),
        Bucket=bucket,
        Key=key
    )
    logging.info("put file s3://{}/{}".format(bucket, key))


def read_user_input(execution_id, bucket, s3_prefix):
    key = f"{s3_prefix}/{execution_id}/user_input.json"
    obj = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(obj['Body'].read())


def sa_optimizer(qubo_data):
    method = 'dwave-sa'
    optimizer_param = {}
    optimizer_param['shots'] = 1000
    sa_optimizer = Annealer(qubo_data, method, **optimizer_param)
    sa_optimizer.fit()
    sa_optimizer.time_summary()
    time_sec = sa_optimizer.time["time-min"] * 60
    logging.info(f"sa_optimizer return time_sec: {time_sec}")
    return time_sec


def read_context(execution_id, bucket, s3_prefix):
    key = f"{s3_prefix}/executions/{execution_id}/user_input.json"
    logging.info("read: s3://{}/{}".format(bucket, key))
    obj = s3.get_object(Bucket=bucket, Key=key)
    context = json.loads(obj['Body'].read())
    logging.info(f"context={context}")
    return context


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--s3-bucket', type=str)
    parser.add_argument('--aws-region', type=str, default=DEFAULT_AWS_REGION)
    parser.add_argument('--resource', type=str),
    parser.add_argument('--execution-id', type=str)
    parser.add_argument('--M', type=int)

    s3_prefix = "molecule-unfolding"

    args, _ = parser.parse_known_args()

    aws_region = args.aws_region
    resource = args.resource
    s3_bucket = args.s3_bucket
    execution_id = args.execution_id

    M = args.M

    model_file = "{}/model/m{}/qubo.pickle".format(s3_prefix, M)

    logging.info("s3_bucket:{}, model_file: {}".format(s3_bucket, model_file))
    logging.info("execution_id: {}".format(execution_id))

    boto3.setup_default_session(region_name=aws_region)
    s3 = boto3.client('s3')

    context = read_context(execution_id, s3_bucket, s3_prefix)
    start_time = context['start_time']
    experiment_name = context['user_input'].get(
        'experimentName', f'{execution_id}|{start_time}')

    local_model_file = download_file(s3_bucket, model_file)

    with open(local_model_file, 'br') as f:
        qubo_data = pickle.load(f)

    time_in_seconds = sa_optimizer(qubo_data)
    task_id = "NA"
    model_name = '_ModelName_'

    metrics_items = [execution_id,
                     "HPC",
                     str(resource),
                     f"M={M}",
                     str(time_in_seconds),
                     start_time,
                     experiment_name,
                     task_id,
                     model_name,
                     s3_prefix,
                      datetime.datetime.utcnow().isoformat()
                     ]
    metrics = ",".join(metrics_items)
    logging.info("metrics='{}'".format(metrics))

    metrics_key = f"{s3_prefix}/benchmark_metrics/{execution_id}-HPC-{resource}-M{M}-{task_id}-{int(time.time())}.csv"
    string_to_s3(metrics, s3_bucket, metrics_key)
    logging.info("Done")
