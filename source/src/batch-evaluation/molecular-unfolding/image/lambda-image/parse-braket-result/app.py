# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from posixpath import basename
import boto3
from botocore import config
import os
import json
import time
import datetime
import logging
from utility.ResultProcess import ResultParser

log = logging.getLogger()
log.setLevel('INFO')

solution_version = os.environ.get('SOLUTION_VERSION', 'v1.0.0')
solution_id = os.environ.get('SOLUTION_ID')
user_agent_config = {
        'user_agent_extra': f'AwsSolution/{solution_id}/{solution_version}'
}
default_config = config.Config(**user_agent_config)

s3 = boto3.client('s3', config=default_config)
step_func = boto3.client('stepfunctions', config=default_config)

s3_prefix = None


def download_file(bucket, key, dir="/tmp/"): #nosec
    file_name = dir + key.split("/")[-1]

    with open(file_name, 'wb') as f:
        s3.download_fileobj(bucket, key, f)
    log.info("download_file: {} -> {}".format(key, file_name))
    return file_name


def download_s3_file(s3_path):
    log.info(f"download_s3_file {s3_path} ...")
    b = s3_path.split("/")[2]
    k = "/".join(s3_path.split("/")[3:])
    return download_file(b, k)


def string_to_s3(content, bucket, key):
    s3.put_object(
        Body=content.encode("utf-8"),
        Bucket=bucket,
        Key=key
    )


def read_as_json(bucket, key):
    #log.info(f"read s3://{bucket}/{key}")
    log.info(f"read_as_json bucket:'{bucket}' key:'{key}'")
    obj = s3.get_object(Bucket=bucket, Key=key)
    json_ = json.loads(obj['Body'].read())
    log.info(f"return: {json_}")
    return json_


def del_local_file(path):
    os.remove(path)


def get_token_for_task_id(qc_task_id, s3_bucket):
    log.info("get_token_for_task_id()")
    key = f"{s3_prefix}/qc_task_token/{qc_task_id}.json"
    n = 0
    while n < 20:
        try:
            return read_as_json(s3_bucket, key)
        except Exception as e:
            if 'the specified key does not exist' in repr(e).lower():
                n = n + 1
                wait_sec = 3 * n + 7
                log.info(f"sleep {wait_sec} ...")
                time.sleep(wait_sec)
            else:
                log.info(f"Error when reading s3://{s3_bucket}/{key}")
                log.info(repr(e))
                raise e
    raise Exception(
        f"error when call get_token_for_task_id: {qc_task_id}, key={key}")


def read_context(execution_id, bucket, s3_prefix):
    key = f"{s3_prefix}/executions/{execution_id}/user_input.json"
    log.info("read: s3://{}/{}".format(bucket, key))
    obj = s3.get_object(Bucket=bucket, Key=key)
    context = json.loads(obj['Body'].read())
    log.info(f"context={context}")
    return context


def task_already_done(execution_id, qc_task_id, bucket):
    key = f"{s3_prefix}/done_task/{execution_id}_{qc_task_id}"
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except Exception as e:
        return False


def upload_result_files(execution_id, task_id, res_files: list, bucket):
    keys = []
    for f in res_files:
        name = basename(f)
        key = f"{s3_prefix}/executions/{execution_id}/result/QC/{task_id}/{name}"
        log.info(f"upload {f} -> {key}")
        s3.upload_file(f, bucket, key)
        keys.append(f"s3://{bucket}/{key}")
        del_local_file(f)
    return keys


def get_result(path):
    with open(path) as f:
        return json.dumps(json.load(f))


def parse_task_result(bucket, key, status='COMPLETED'):
    log.info(f"parse_task_result() bucket: {bucket}, key: {key}, status: {status}")
    global s3_prefix
    s3_prefix = key.split('/qc_task_output/')[0]

    qc_task_id = key.split("/")[-2]
    log.info(f"qc_task_id: {qc_task_id}")
    prefix = "/".join(key.split("/")[:-2])

    task_info = get_token_for_task_id(qc_task_id, bucket)

    if not task_info:
        return

    execution_id = task_info['execution_id']
    task_token = task_info['task_token']
    submit_result = task_info['submit_result']

    if status != 'COMPLETED':
       return step_func.send_task_failure(
                taskToken=task_token,
                error= f"braket task status: {status}",
                cause='ParseBraketResultLambda'
            )


    if task_already_done(execution_id, qc_task_id, bucket):
        log.info(f"qc_task_id={qc_task_id} already done")
        return

    message = None
    try:

        index = submit_result['index']
        model_info = submit_result['model_info']
        data_s3_path = model_info['data']
        raw_s3_path = model_info['raw']

        data_local_path = download_s3_file(data_s3_path)
        raw_local_path = download_s3_file(raw_s3_path)

        log.info(
            f"ResultParser(task_id={qc_task_id}, prefix={prefix}, data_path={data_local_path}, raw_path={raw_local_path}) ...")
        qa_process_result = ResultParser('dwave-qa',
                                         bucket=bucket,
                                         prefix=prefix,
                                         task_id=qc_task_id,
                                         data_path=data_local_path,
                                         raw_path=raw_local_path
                                         )

        local_time, task_time, total_time, access_time = qa_process_result.get_time()

        log.info(
            f"local_time={local_time}, task_time={task_time}, total_time={total_time}, access_time={access_time}")

        log.info("generate_optimize_pts()")
        timestamp = int(time.time())
        qa_atom_pos_data = qa_process_result.generate_optimize_pts()
        log.info(f"qa_atom_pos_data: {qa_atom_pos_data}")
        result_files = qa_process_result.save_mol_file(f"{timestamp}")
        result_json = get_result(result_files[1])
        result_s3_files = upload_result_files(
            execution_id, qc_task_id, result_files, bucket)
        log.info(f"result_s3_files: {result_s3_files}")
        del_local_file(data_local_path)
        del_local_file(raw_local_path)

        model_param = submit_result['model_param']
        complexity = submit_result['complexity']
        model_name = submit_result['model_name']
        mode_file_name = submit_result['mode_file_name']
        start_time = submit_result['start_time']
        experiment_name = submit_result['experiment_name']
        device_name = submit_result['device_name']
        local_fit_time = submit_result['local_fit_time']
        optimizer_param = submit_result['optimizer_param']

        end_to_end_time = local_fit_time
        running_time = total_time
        task_id = qc_task_id

        time_info_json = json.dumps({
            "task_time": task_time,
            "total_time": total_time,
            "local_time": local_time,
            "access_time": access_time
        })

        resolver = f"QC {device_name}" 
        if device_name in [ 'DW_2000Q_6', 'Advantage_system4', 'Advantage_system6']:
            resolver = f"QC D-Wave {device_name}" 

        metrics_items = [execution_id,
                     "QC",
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
                     device_name,
                     model_param,
                     json.dumps(optimizer_param),
                     datetime.datetime.utcnow().isoformat(),
                     result_json,
                     result_s3_files[0]
                     ]

        metrics = "\t".join(metrics_items)
        log.info("metrics='{}'".format(metrics))
        metrics_key = f"{s3_prefix}/batch_evaluation_metrics/{execution_id}-QC-{device_name}-{model_name}-{index}-{qc_task_id}.csv"
        string_to_s3(metrics, bucket, metrics_key)
        string_to_s3("Done", bucket,
                     key=f"{s3_prefix}/done_task/{execution_id}_{qc_task_id}")
        message = metrics_key
        success = True
    except Exception as e:
        string_to_s3(repr(e), bucket,
                     key=f"{s3_prefix}/err_task/{execution_id}_{qc_task_id}")
        log.info(repr(e))
        message = repr(e)
        success = False

    try:
        log.info(
            f"send call back for qc_task_id: {qc_task_id}, task_token: {task_token}")
        if success:
            step_func.send_task_success(
                taskToken=task_token,
                output=json.dumps({
                    'message': message,
                    'task_id': qc_task_id
                }))
        else:
            step_func.send_task_failure(
                taskToken=task_token,
                error=message,
                cause='ParseBraketResultLambda'
            )

    except Exception as e:
        log.info(repr(e))


def handle_event_bridge_message(event):
    region = os.environ['AWS_REGION']
    outputS3Bucket = event['detail']['outputS3Bucket']

    if not str(outputS3Bucket).endswith(region):
        log.info(f'reqeust is not from my resion: {region}, ignore message, outputS3Bucket: {outputS3Bucket}')
        return 

    outputS3Directory = event['detail']['outputS3Directory']
    status = event['detail']['status']
    log.info(f"status={status}")
    key = f"{outputS3Directory}/result.json"
    if status in ['COMPLETED', 'FAILED']:
        parse_task_result(outputS3Bucket, key, status)
    else:
        log.info(f"ignore status={status}")


def handler(event, context):
    log.info(f"event={event}")
    if 'detail-type' in event:
        handle_event_bridge_message(event)
    else:

        #
        # S3 event
        #

        # {'Records': [{'eventVersion': '2.1', 'eventSource': 'aws:s3', 'awsRegion': 'us-east-1', 'eventTime': '2021-11-29T05:17:52.234Z', 'eventName': 'ObjectCreated:Put', 'userIdentity': {'principalId': 'AWS:AROARFTQUWKOUWSYO5XRB:AWSServiceRoleForAmazonBraket'}, 'requestParameters': {'sourceIPAddress': '52.25.248.119'}, 'responseElements': {'x-amz-request-id': '1FQTNJ9HM86M7DMY', 'x-amz-id-2': 'UW1UEJKmwy6NcYRFnTafQSpD4sx05nAOxgs+YtEBH6ryx2MEGbXUj4nAW1ROIs6qtT2D12KCrcDMaKMnIDynCtLmwKAVQu8p'}, 's3': {'s3SchemaVersion': '1.0', 'configurationId': 'ZmNmMzBiZTktNTJiNi00YTllLTk1ODQtYjQyMWI1MzU2OTMw', 'bucket': {'name': 'amazon-braket-qcstack-main-080766874269-us-east-1', 'ownerIdentity': {'principalId': 'AKDTHGWL4N5KF'}, 'arn': 'arn:aws:s3:::amazon-braket-qcstack-main-080766874269-us-east-1'}, 'object': {'key': 'molecular-unfolding/qc_task_output/2fb927dc-32af-42a1-8517-b0872fa4e921/results.json', 'size': 16475, 'eTag': 'd86bf699fb617e1e03ea704695173f13', 'sequencer': '0061A462802499277F'}}}]}
        for rec in event['Records']:
            bucket = rec['s3']['bucket']['name']
            key = rec['s3']['object']['key']
            log.info(f"parsing file: s3://{bucket}/{key}")
            parse_task_result(bucket, key)
