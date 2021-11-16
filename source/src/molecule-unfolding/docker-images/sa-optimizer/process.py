import argparse
import logging
import boto3
import time
import pickle
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


def sa_optimizer(qubo_data):
    method = 'dwave-sa'
    optimizer_param = {}
    optimizer_param['shots'] = 1000
    sa_optimizer = Annealer(qubo_data, method, **optimizer_param)
    sa_optimizer.fit()
    sa_optimizer.time_summary()
    time_min= sa_optimizer.time["time-min"]
    logging.info(f"sa_optimizer return time_min: {time_min}")
    return time_min


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--s3-bucket', type=str)
    parser.add_argument('--aws-region', type=str, default=DEFAULT_AWS_REGION)
    parser.add_argument('--resource', type=str)
    parser.add_argument('--M', type=int)
    
    s3_prefix = "molecule-unfolding"

    args, _ = parser.parse_known_args()

    aws_region = args.aws_region
    resource = args.resource
    s3_bucket = args.s3_bucket
    M = args.M
    
    model_file = "{}/model/m{}/qubo.pickle".format(s3_prefix, M)

    logging.info("s3_bucket:{}, model_file: {}".format(s3_bucket, model_file))
    
    boto3.setup_default_session(region_name=aws_region)
    s3 = boto3.client('s3')

    local_model_file = download_file(s3_bucket, model_file)

    with open(local_model_file, 'br') as f:
        qubo_data = pickle.load(f)

    time_in_mins = sa_optimizer(qubo_data)

    metrics_items = ["HPC", str(resource), str(M), str(time_in_mins)]
    metrics = ",".join(metrics_items)
    logging.info("metrics='{}'".format(metrics))

    metrics_key = "{}/metrics/{}-{}-M{}-{}.csv".format(
        s3_prefix, "HPC", resource, M, int(time.time()))
    string_to_s3(metrics, s3_bucket, metrics_key)
    logging.info("Done")
