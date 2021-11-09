import argparse
import logging
import boto3
import time
import json
from utility.AnnealerOptimizer import Annealer


logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.INFO)

DEFAULT_AWS_REGION = 'us-east-1'


def download_file(bucket, key, dir="./"):
    s3 = boto3.client('s3')
    file_name = dir + key.split("/")[-1]

    with open(file_name, 'wb') as f:
        s3.download_fileobj(bucket, key, f)
    logging.info("download_file: {} -> {}".format(key, file_name))

    return file_name


def string_to_s3(content, bucket, key):
    s3 = boto3.client('s3')
    s3.put_object(
        Body=content.encode("utf-8"),
        Bucket=bucket,
        Key=key
    )
    logging.info("put file s3://{}/{}".format(bucket, key))


def sa_optimizer(qubo_data):
    method = 'dwave-sa'
    optimizer_param = {}
    optimizer_param['shots'] = 1000
    sa_optimizer = Annealer(qubo_data, method, **optimizer_param)
    sa_optimizer.fit()
    return sa_optimizer.time_summary()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--s3-bucket', type=str)
    parser.add_argument('--aws-region', type=str, default=DEFAULT_AWS_REGION)
    parser.add_argument('--resource', type=str)
    parser.add_argument('--model-file', type=str)

    args, _ = parser.parse_known_args()

    aws_region = args.aws_region
    resource = args.resource
    s3_bucket = args.s3_bucket
    model_file = args.model_file

    logging.info("s3_bucket:{}, model_file: {}".format(s3_bucket, model_file))

    s3_prefix = "molecule-unfolding"
    boto3.setup_default_session(region_name=aws_region)

    param_file = "/".join(model_file.split("/")[:-1]) + "/param.json"
    local_model_file = download_file(s3_bucket, model_file)
    local_param_file = download_file(s3_bucket, param_file)

    with open(local_model_file, 'r') as f:
        qubo_data = json.load(f)

    time_in_mins = sa_optimizer(qubo_data)

    params = json.load(local_param_file)
    M = params['M']
    metrics_items = ["HPC", str(resource), str(M), str(time_in_mins)]
    metrics = ",".join(metrics_items)
    logging.info("metrics='{}'".format(metrics))

    metrics_key = "{}/metrics/{}-{}-M{}-{}.csv".format(
        s3_prefix, "HPC", resource, M, int(time.time()))
    string_to_s3(metrics, s3_bucket, metrics_key)
    logging.info("Done")
