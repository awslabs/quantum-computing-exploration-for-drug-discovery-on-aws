# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import argparse
import logging
import boto3
import time
import datetime
import os
import json
from os.path import basename

from utility.AnnealerOptimizer import Annealer
from utility.QMUQUBO import QMUQUBO
from utility.ResultProcess import ResultParser

sa_optimizer_method = 'neal-sa'

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.INFO)


def download_file(bucket, key, dir="./"):
    file_name = dir + key.split("/")[-1]

    with open(file_name, 'wb') as f:
        s3.download_fileobj(bucket, key, f)
    logging.info("download_file: {} -> {}".format(key, file_name))
    return file_name


def upload_file(bucket, key, file_name):
    s3.upload_file(file_name, bucket, key)
    logging.info(f"upload_file {file_name} -> s3://{bucket}/{key}")
    return f"s3://{bucket}/{key}"


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


def download_file(bucket, key, dir="/tmp/"): #nosec
    file_name = dir + key.split("/")[-1]

    with open(file_name, 'wb') as f:
        s3.download_fileobj(bucket, key, f)
    print("download_file: {} -> {}".format(key, file_name))
    return file_name


def download_s3_file(s3_path):
    print(f"download_s3_file {s3_path} ...")
    b = s3_path.split("/")[2]
    k = "/".join(s3_path.split("/")[3:])
    return download_file(b, k)


def upload_result_files(execution_id, param_info, res_files: list, bucket):
    keys = []
    for f in res_files:
        name = basename(f)
        key = f"{s3_prefix}/executions/{execution_id}/result/CC/{param_info}/{name}"
        print(f"upload {f} -> {key}")
        s3.upload_file(f, bucket, key)
        keys.append(f"s3://{bucket}/{key}")
    return keys     


def sa_optimizer(qubo_model, model_file_info, param_info):
    method = sa_optimizer_method
    optimizer_param = {}

    optimizer_param['shots'] =  10000
    optimizer_param['notes'] =  'batch evaluation'

    optimizer_params = context['user_input'].get('optParams', None)
    if optimizer_params and optimizer_params.get('sa', None):
        user_optimizer_param = optimizer_params.get('sa')
        optimizer_param['shots'] = user_optimizer_param.get('shots', 10000)
        optimizer_param['notes'] =  user_optimizer_param.get('notes', 'batch evaluation')
    
    sa_optimizer = Annealer(qubo_model, method, **optimizer_param)
    sa_optimize_result = sa_optimizer.fit()
    time_sec = sa_optimize_result['time']
    logging.info(f"sa_optimizer return time_sec: {time_sec}")

    raw_s3_path = model_file_info['raw']
    data_s3_path = model_file_info['data']
    raw_path = download_s3_file(raw_s3_path)
    data_path = download_s3_file(data_s3_path)
    
    sa_param = {}
    sa_param["raw_path"] = raw_path
    sa_param["data_path"] = data_path
    
    sa_process_result = ResultParser(method, **sa_param)
    logging.info(f"{method} result is {sa_process_result.get_all_result()}")
    local_time, _ , _, _= sa_process_result.get_time()

    sa_atom_pos_data = sa_process_result.generate_optimize_pts()
    timestamp = int(time.time())
    result_files = sa_process_result.save_mol_file(f"{timestamp}")  

    result_json = get_result(result_files[1])

    result_s3_files = upload_result_files(execution_id, param_info, result_files, s3_bucket)

    return { 'fit_time': time_sec, 'local_time': local_time,
     'result_s3_files': result_s3_files,
     'result_json': result_json,
     'optimizer_param': optimizer_param
     }


def read_context(execution_id, bucket, s3_prefix):
    key = f"{s3_prefix}/executions/{execution_id}/user_input.json"
    logging.info("read: s3://{}/{}".format(bucket, key))
    obj = s3.get_object(Bucket=bucket, Key=key)
    context = json.loads(obj['Body'].read())
    logging.info(f"context={context}")
    return context


def get_model_info(execution_id):
    key = f"{s3_prefix}/executions/{execution_id}/model_info.json"
    obj = s3.get_object(Bucket=s3_bucket, Key=key)
    model_file_info = json.loads(obj['Body'].read())
    return model_file_info


def load_model(model_input_file, model_param):
    logging.info(f"load_model() {model_input_file}, model_param={model_param}")
    if model_input_file.startswith("s3://"):
        model_file = "/".join(model_input_file.split("/")[3:])
        s3bucket = model_input_file.split("/")[2]
    else:
        s3bucket = s3_bucket
        model_file = model_input_file

    logging.info(f"download s3://{s3bucket}/{model_file}")

    local_model_file = download_file(s3bucket, model_file)
    mode_file_name = os.path.basename(local_model_file)
    qmu_qubo_optimize = QMUQUBO.load(local_model_file)
    model_info = qmu_qubo_optimize.describe_model()

    logging.info(f"get_model model_info={model_info}")

    # D = 4
    # A = 300
    # hubo_qubo_val = 200
    # model_name = "{}_{}_{}_{}".format(M, D, A, hubo_qubo_val)

    model_name = "_".join(
        map(lambda it: it.split("=")[1], model_param.split('&')))
    logging.info(f"model_name:{model_name}")

    M =  model_param.split('&')[0].split('=')[1]
    D =  model_param.split('&')[1].split('=')[1]
    complexity = int(M) * int(D)
    logging.info("M={}, D={}, complexity={}".format(M, D, complexity))

    method = "pre-calc"
    logging.info(f"get_model model_name={model_name}, method={method}")
    qubo_model = qmu_qubo_optimize.get_model(method, model_name)
    return qubo_model, model_name, mode_file_name, complexity

def get_result(path):
    with open(path) as f:
        return json.dumps(json.load(f))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--s3-bucket', type=str)
    parser.add_argument('--aws-region', type=str)
    parser.add_argument('--resource', type=str),
    parser.add_argument('--execution-id', type=str)
    parser.add_argument('--model-param', type=str)
    parser.add_argument('--index', type=str)
    parser.add_argument('--s3_prefix', type=str)


    args, _ = parser.parse_known_args()

    aws_region = args.aws_region
    resource = args.resource
    s3_bucket = args.s3_bucket
    execution_id = args.execution_id
    index = args.index
    s3_prefix = args.s3_prefix

    model_param = args.model_param

    logging.info("execution_id: {}, model_param:{}".format(
        execution_id, model_param))

    param_info = f"{model_param}_{resource}"    

    boto3.setup_default_session(region_name=aws_region)
    s3 = boto3.client('s3')

    context = read_context(execution_id, s3_bucket, s3_prefix)
    start_time = context['start_time']

    experiment_name = context['user_input'].get('experimentName', None)
    if experiment_name is None:
        experiment_name = f"{start_time}_{execution_id}"
    else:
        experiment_name = f"{start_time}_{experiment_name}"

    model_file_info = get_model_info(execution_id)
    logging.info("model_file: {}".format(model_file_info))

    qubo_model, model_name, mode_file_name, complexity = load_model(
        model_file_info['model'], model_param)

    sa_result = sa_optimizer(qubo_model, model_file_info, param_info)
    task_id = ""
    local_time = sa_result['local_time']
    result_s3_files = sa_result['result_s3_files']
    result_json = sa_result['result_json']
    optimizer_param =  sa_result['optimizer_param']

    end_to_end_time = local_time
    running_time = local_time
    time_info_json = json.dumps({
                                 "local_time": local_time
                             })
    
    #result_file_info = json.dumps(result_s3_files)
    resolver = 'CC ' + sa_optimizer_method.upper()

    metrics_items = [execution_id,
                     "CC",
                     resolver,
                     str(complexity),
                     str(end_to_end_time),
                     str(running_time),
                     time_info_json,
                     start_time,
                     experiment_name,
                     task_id,
                     model_name,
                     mode_file_name,
                     s3_prefix,
                     str(resource),
                     model_param,
                     json.dumps(optimizer_param),
                     datetime.datetime.utcnow().isoformat(),
                     result_json,
                     result_s3_files[0]
                     ]
    metrics = "\t".join(metrics_items)
    logging.info("metrics='{}'".format(metrics))

    metrics_key = f"{s3_prefix}/batch_evaluation_metrics/{execution_id}-CC-{resource}-{model_name}-{index}-{int(time.time())}.csv"
    string_to_s3(metrics, s3_bucket, metrics_key)
    logging.info("Done")
