import argparse
import logging
import pickle
import boto3
import json
import time
from utility.AnnealerOptimizer import Annealer


logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.INFO)

DEFAULT_DEVICE_ARN = 'arn:aws:braket:::device/qpu/d-wave/Advantage_system4'
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


def list_files(s3_bucket, s3_prefix):
    logging.inf("list_files - s3://{}/{}".format(s3_bucket, s3_prefix))
    partial_list = s3.list_objects_v2(
        Bucket=s3_bucket,
        Prefix=s3_prefix)

    obj_list = partial_list['Contents']

    while partial_list['IsTruncated']:
        next_token = partial_list['NextContinuationToken']
        partial_list = s3.list_objects_v2(
            Bucket=s3_bucket,
            Prefix=s3_prefix,
            ContinuationToken=next_token)

        obj_list.extend(partial_list['Contents'])

    logging.info(
        "list_files: find {} objects in s3://{}/{}".format(len(obj_list), s3_bucket, s3_prefix))
    return obj_list


def qa_optimizer(qubo_data, s3_bucket, s3_prefix, device_arn):
    method = 'dwave-qa'
    optimizer_param = {}
    optimizer_param['shots'] = 1000
    optimizer_param['bucket'] = s3_bucket
    optimizer_param['prefix'] = s3_prefix
    optimizer_param['device'] = device_arn
    optimizer_param["embed_method"] = "default"
    qa_optimizer = Annealer(qubo_data, method, **optimizer_param)
    qa_optimizer.embed()
    qa_optimizer.fit()
    qa_optimizer.time_summary()
    time_min =  qa_optimizer.time["time-min"]
    logging.info(f"qa_optimizer return time_min: {time_min}")
    return time_min


def run_on_device(model_file, device_arn, M):
    logging.info(
        "run_on_device() - model_file:{}, device_arn: {}, M: {}".format(model_file, device_arn, M))
    local_model_file = download_file(s3_bucket, model_file)

    with open(local_model_file, 'br') as f:
        qubo_data = pickle.load(f)

    time_in_mins = qa_optimizer(qubo_data, s3_bucket, s3_prefix, device_arn)
    
    device_name = device_arn.split("/")[-1]

    metrics_items = ["QC", str(device_name), str(M), str(time_in_mins)]
    metrics = ",".join(metrics_items)
    logging.info("metrics='{}'".format(metrics))
    metrics_key = "{}/metrics/{}-M{}-{}-{}.csv".format(
        s3_prefix, "QC", M, device_name,int(time.time()))

    string_to_s3(metrics, s3_bucket, metrics_key)

    return metrics


def string_to_s3(content, bucket, key):
    s3.put_object(
        Body=content.encode("utf-8"),
        Bucket=bucket,
        Key=key
    )
def read_user_input(execution_id, bucket, s3_prefix):
    key= f"{s3_prefix}/{execution_id}/user_input.json"
    obj = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(obj['Body'].read())


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--s3-bucket', type=str)
    parser.add_argument('--aws-region', type=str, default=DEFAULT_AWS_REGION)
    parser.add_argument('--device-arn', type=str, default='arn:aws:braket:::device/qpu/d-wave/Advantage_system4')
    parser.add_argument('--M', type=int)
    
    s3_prefix = "molecule-unfolding"

    args, _ = parser.parse_known_args()

    aws_region = args.aws_region
    device_arn = args.device_arn
    s3_bucket = args.s3_bucket
    M = args.M
    
    model_file = "{}/model/m{}/qubo.pickle".format(s3_prefix, M)

    boto3.setup_default_session(region_name=aws_region)
    s3 = boto3.client('s3')

    run_on_device(model_file, device_arn, M)

    logging.info("Done")
