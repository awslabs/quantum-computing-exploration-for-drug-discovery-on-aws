import argparse
import logging
import boto3
import time
import json
from utility.AnnealerOptimizer import Annealer


logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.INFO)

DEFAULT_DEVICE_ARN = 'arn:aws:braket:::device/qpu/d-wave/Advantage_system4'
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


def list_files(s3_bucket, s3_prefix):
    logging.inf("list_files - s3://{}/{}".format(s3_bucket, s3_prefix))

    s3 = boto3.client('s3')
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
    return qa_optimizer.time_summary()


def run_on_device(model_file, device_arn):
    logging.info(
        "run_on_device() - model_file:{}, device_arn: {}".format(model_file, device_arn))
    param_file = "/".join(model_file.split("/")[:-1]) + "/param.json"
    local_model_file = download_file(s3_bucket, model_file)
    local_param_file = download_file(s3_bucket, param_file)

    with open(local_model_file, 'r') as f:
        qubo_data = json.load(f)

    time_in_mins = qa_optimizer(qubo_data, s3_bucket, s3_prefix, device_arn)

    device_name = device_arn.split("/")[-1]
    params = json.load(local_param_file)
    M = params['M']

    metrics_items = ["QC", str(device_name), str(M), str(time_in_mins)]
    metrics = ",".join(metrics_items)
    logging.info("metrics='{}'".format(metrics))
    return metrics


def run_all_on_devices(s3_bucket):
    s3_prefix = "molecule-unfolding"
    model_file_dir = "{}/model/".s3_prefix(s3_prefix)

    logging.info("s3_bucket:{}, model_file_dir: {}".format(
        s3_bucket, model_file_dir))

    model_files = [model_file for model_file in
                   list_files(s3_bucket, model_file_dir) if str(model_file).endswith("qubo.json")]
    device_arns = [
        'arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6',
        'arn:aws:braket:::device/qpu/d-wave/Advantage_system4'
    ]
    metrics_lines = []
    for model_file in model_files:
        for device_arn in device_arns:
            metrics_line = run_on_device(model_file, device_arn)
            metrics_lines.append(metrics_line)

    metrics_key = "{}/metrics/{}-{}.csv".format(
        s3_prefix, "QC", int(time.time()))

    string_to_s3("\n".join(metrics_lines), s3_bucket, metrics_key)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--s3-bucket', type=str)
    parser.add_argument('--aws-region', type=str, default=DEFAULT_AWS_REGION)

    args, _ = parser.parse_known_args()

    aws_region = args.aws_region
    device_arn = args.device_arn
    s3_bucket = args.s3_bucket
    boto3.setup_default_session(region_name=aws_region)
    run_all_on_devices(s3_bucket)
    logging.info("Done")
