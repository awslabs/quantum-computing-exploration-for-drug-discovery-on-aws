# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import argparse
import logging
import boto3
import json
import time
import os
import uuid
from utility.AnnealerOptimizer import Annealer
from utility.QMUQUBO import QMUQUBO


logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.INFO)

DEFAULT_DEVICE_ARN = 'arn:aws:braket:::device/qpu/d-wave/Advantage_system4'
DEFAULT_AWS_REGION = 'us-east-1'

logging_info = print


def download_file(s3, bucket, key, dir="/tmp/"): #nosec
    file_name = dir + key.split("/")[-1]

    with open(file_name, 'wb') as f:
        s3.download_fileobj(bucket, key, f)
    logging_info("download_file: {} -> {}".format(key, file_name))

    return file_name


def string_to_s3(s3, content, bucket, key):
    s3.put_object(
        Body=content.encode("utf-8"),
        Bucket=bucket,
        Key=key
    )
    logging_info("put file s3://{}/{}".format(bucket, key))


def list_files(s3, s3_bucket, s3_prefix):
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

    logging_info(
        "list_files: find {} objects in s3://{}/{}".format(len(obj_list), s3_bucket, s3_prefix))
    return obj_list


def get_qc_task_id(response):
    return f"qc-task-id-{time.time()}-{uuid.uuid1().hex}"


def qa_optimizer(context, execution_id, qubo_model, s3_bucket, task_output_s3_prefix, s3_prefix, device_arn):
    method = 'dwave-qa'
    optimizer_param = {}
    optimizer_param['shots'] = 10000
    optimizer_param['bucket'] = s3_bucket
    optimizer_param['prefix'] = task_output_s3_prefix
    optimizer_param['device'] = device_arn
    optimizer_param["embed_method"] = "default"
    #qa_optimizer = Annealer(qubo_model['qubo'], method, **optimizer_param)

    optimizer_params = context['user_input'].get('optParams', None)
    if optimizer_params and optimizer_params.get('qa', None):
        user_optimizer_param = optimizer_params.get('qa')
        optimizer_param['shots'] = user_optimizer_param.get('shots', 10000)
        optimizer_param['embed_method'] =  user_optimizer_param.get('embed_method', 'default')


    rt_optimizer_param = optimizer_param.copy()
    for k in ['bucket', 'prefix', 'device']:
        del rt_optimizer_param[k]

    qa_optimizer = Annealer(qubo_model, method, **optimizer_param)
    qa_optimizer.embed()

    qa_optimize_result = qa_optimizer.fit()
    local_fit_time = qa_optimize_result['time']

    qc_task_id = qa_optimizer.get_task_id()
    logging_info(f"qa_optimizer() return qc_task_id: {qc_task_id}, local_fit_time:{local_fit_time}")
    return qc_task_id, local_fit_time, rt_optimizer_param


def run_on_device(s3, input_params):
    logging_info(
        "run_on_device() - input_params: {}".format(input_params))

    context = input_params['context']
    model_file = input_params['model_file']
    model_param = input_params['model_param']
    s3_bucket = input_params['s3_bucket']
    s3_prefix = input_params['s3_prefix']
    experiment_name = input_params['experiment_name']
    start_time = input_params['start_time']
    device_arn = input_params['device_arn']
    execution_id = input_params['execution_id']

    qubo_model, model_name, mode_file_name, complexity = load_model(
        s3, model_file, model_param, s3_bucket)

    task_output = f"{s3_prefix}/qc_task_output"
    qc_task_id, local_fit_time, optimizer_param = qa_optimizer(
        context,
        execution_id,
        qubo_model,
        s3_bucket,
        task_output,
        s3_prefix,
        device_arn)

    device_name = device_arn.split("/")[-1]
    task_id = qc_task_id

    logging_info(
        "run_on_device() return - task_id:{}".format(task_id))
    return {
        "execution_id": execution_id,
        "task_id": task_id,
        "model_name": model_name,
        "mode_file_name": mode_file_name,
        "experiment_name": experiment_name,
        "start_time": start_time,
        "model_param": model_param,
        "complexity": complexity,
        "device_name": device_name,
        "local_fit_time": local_fit_time,
        "optimizer_param": optimizer_param
    }


def string_to_s3(s3, content, bucket, key):
    s3.put_object(
        Body=content.encode("utf-8"),
        Bucket=bucket,
        Key=key
    )


def read_context(s3, execution_id, bucket, s3_prefix):
    key = f"{s3_prefix}/executions/{execution_id}/user_input.json"
    logging_info("read: s3://{}/{}".format(bucket, key))
    obj = s3.get_object(Bucket=bucket, Key=key)
    context = json.loads(obj['Body'].read())
    logging_info(f"context={context}")
    return context


def get_model_info(s3, execution_id, s3_bucket, s3_prefix):
    key = f"{s3_prefix}/executions/{execution_id}/model_info.json"
    obj = s3.get_object(Bucket=s3_bucket, Key=key)
    model_info = json.loads(obj['Body'].read())
    return model_info


def load_model(s3, model_input_file, model_param, s3_bucket):
    logging_info(f"load_model() {model_input_file}, model_param={model_param}")
    if model_input_file.startswith("s3://"):
        model_file = "/".join(model_input_file.split("/")[3:])
        s3bucket = model_input_file.split("/")[2]
    else:
        s3bucket = s3_bucket
        model_file = model_input_file

    logging_info(f"download s3://{s3bucket}/{model_file}")

    local_model_file = download_file(s3, s3bucket, model_file)

    model_file_name = os.path.basename(local_model_file)

    qmu_qubo_optimize = QMUQUBO.load(local_model_file)
    model_info = qmu_qubo_optimize.describe_model()

    logging_info(f"get_model model_info={model_info}")

    # D = 4
    # A = 300
    # hubo_qubo_val = 200
    # model_param = 'M=1&D=4&A=300&HQ=200'
    # model_name = "{}_{}_{}_{}".format(M, D, A, hubo_qubo_val)
    model_name = "_".join(
        map(lambda it: it.split("=")[1], model_param.split('&')))
    logging_info(f"model_name:{model_name}")

    M =  model_param.split('&')[0].split('=')[1]
    D =  model_param.split('&')[1].split('=')[1]
    complexity = int(M) * int(D)
    logging.info("M={}, D={}, complexity={}".format(M, D, complexity))

    method = "pre-calc"
    logging_info(f"get_model model_name={model_name}, method={method}")
    qubo_model = qmu_qubo_optimize.get_model(method, model_name)
    return qubo_model, model_name, model_file_name, complexity


def submit_qc_task(s3, execution_id, device_arn, model_param, s3_bucket, s3_prefix):

    model_info = get_model_info(s3, execution_id, s3_bucket, s3_prefix)

    logging_info("model_info: {}".format(model_info))

    context = read_context(s3, execution_id, s3_bucket, s3_prefix)
    start_time = context['start_time']

    experiment_name = context['user_input'].get('experimentName', None)
    if experiment_name is None:
        experiment_name = f"{start_time}_{execution_id}"
    else:
        experiment_name = f"{start_time}_{experiment_name}"
    
    # {"task_id": task_id, "model_name": model_name,  "mode_file_name": mode_file_name}
    res = run_on_device(s3, {
        "context": context,
        "execution_id": execution_id,
        "model_file": model_info['model'],
        "device_arn": device_arn,
        "model_param": model_param,
        "s3_bucket": s3_bucket,
        "s3_prefix": s3_prefix,
        "start_time": start_time,
        "experiment_name": experiment_name})

    res['model_info'] = model_info
    logging_info("submit_qc_task return: {}".format(res))

    return res


def save_sumbit_result(execution_id, batch_job_id,  qc_task_id, submit_result, s3_bucket):
    print("save_sumbit_result() ")
    key = f"{s3_prefix}/executions/{execution_id}/qa_batch_jobs/{batch_job_id}.json"
    string_to_s3(s3, json.dumps({
        "execution_id": execution_id,
        "qc_task_id": qc_task_id,
        "batch_job_id": batch_job_id,
        "submit_result": submit_result
    }), s3_bucket, key)
    print(f"saved s3://{s3_bucket}/{key}")



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--s3-bucket', type=str)
    parser.add_argument('--aws-region', type=str)
    parser.add_argument('--device-arn', type=str),
    parser.add_argument('--execution-id', type=str)
    parser.add_argument('--model-param', type=str)
    parser.add_argument('--index', type=str)
    parser.add_argument('--s3_prefix', type=str)


    args, _ = parser.parse_known_args()

    aws_region = args.aws_region
    device_arn = args.device_arn
    s3_bucket = args.s3_bucket
    execution_id = args.execution_id
    index = args.index
    s3_prefix = args.s3_prefix

    model_param = args.model_param

    logging.info("execution_id: {}, model_param:{}".format(
        execution_id, model_param))

    boto3.setup_default_session(region_name=aws_region)
    s3 = boto3.client('s3')

    submit_result = submit_qc_task(s3, execution_id, device_arn,
                                model_param, s3_bucket, s3_prefix)
    submit_result['index'] = index
    # {"task_id": task_id, "model_name": model_name,  "mode_file_name": mode_file_name}
    qc_task_id = submit_result['task_id']

    print(f"qc_task_id={qc_task_id}")

    batch_job_id = os.environ['AWS_BATCH_JOB_ID']

    save_sumbit_result(execution_id, batch_job_id, qc_task_id,
                           submit_result, s3_bucket)




