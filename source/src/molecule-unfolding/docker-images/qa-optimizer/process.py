import argparse
import logging
import pickle
import boto3
import json
import time
import datetime
import os


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

def get_qc_task_id(response):
    return "qc-task-id-{int(time.time())}"

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

    response = qa_optimizer.fit()
    logging.info(f"fit response:{response}")

    qc_task_id = get_qc_task_id(response)

    string_to_s3(json.dumps({
        'batch_job_id': batch_job_id,
        'qc_task_id': qc_task_id,
        'execution_id': execution_id
    }), s3_bucket, key=f"f{s3_prefix}/batch_job_and_qc_task_map/{batch_job_id}.json")

    qa_optimizer.time_summary()
    time_sec = qa_optimizer.time["time-min"] * 60
    logging.info(f"qa_optimizer return time_sec: {time_sec}")
    return time_sec


def run_on_device(model_file, device_arn, M):
    logging.info(
        "run_on_device() - model_file:{}, device_arn: {}, M: {}".format(model_file, device_arn, M))
    local_model_file = download_file(s3_bucket, model_file)

    with open(local_model_file, 'br') as f:
        qubo_data = pickle.load(f)

    task_output = f"{s3_prefix}/qc_task_output"
    time_in_seconds = qa_optimizer(qubo_data, s3_bucket, task_output, device_arn)

    device_name = device_arn.split("/")[-1]
    task_id = "NA"
    model_name = '_ModelName_'
    metrics_items = [execution_id,
                     "QC",
                     str(device_name),
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
    metrics_key = f"{s3_prefix}/benchmark_metrics/{execution_id}-HPC-{device_name}-M{M}-{task_id}-{int(time.time())}.csv"
    string_to_s3(metrics, s3_bucket, metrics_key)
    return metrics


def string_to_s3(content, bucket, key):
    s3.put_object(
        Body=content.encode("utf-8"),
        Bucket=bucket,
        Key=key
    )


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
    parser.add_argument('--device-arn', type=str,
                        default='arn:aws:braket:::device/qpu/d-wave/Advantage_system4')
    parser.add_argument('--M', type=int)
    parser.add_argument('--execution-id', type=str)

    s3_prefix = "molecule-unfolding"

    args, _ = parser.parse_known_args()

    aws_region = args.aws_region
    device_arn = args.device_arn
    s3_bucket = args.s3_bucket
    execution_id = args.execution_id
    M = args.M

    logging.info("execution_id: {}".format(execution_id))

    model_file = "{}/model/m{}/qubo.pickle".format(s3_prefix, M)

    boto3.setup_default_session(region_name=aws_region)
    s3 = boto3.client('s3')

    batch_job_id = os.environ['AWS_BATCH_JOB_ID']
    logging.info("batch_jod_id: {}".format(batch_job_id))

    context = read_context(execution_id, s3_bucket, s3_prefix)
    start_time = context['start_time']
    experiment_name = context['user_input'].get(
        'experimentName', f'{execution_id}|{start_time}')

    run_on_device(model_file, device_arn, M)

    logging.info("Done")
