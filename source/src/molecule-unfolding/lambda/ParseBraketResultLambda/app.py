from posixpath import basename
import boto3
import os
import json
import time
import datetime
from utility.ResultProcess import ResultParser

s3 = boto3.client('s3')
s3_prefix = "molecule-unfolding"
step_func = boto3.client('stepfunctions')


def download_file(bucket, key, dir="/tmp/"):
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
    

def string_to_s3(content, bucket, key):
    s3.put_object(
        Body=content.encode("utf-8"),
        Bucket=bucket,
        Key=key
    )


def read_as_json(bucket, key):
    print(f"read s3://{bucket}/{key}")
    obj = s3.get_object(Bucket=bucket, Key=key)
    json_ = json.loads(obj['Body'].read())
    print(f"return: {json_}")
    return json_


def del_local_file(path):
    os.remove(path)


def get_token_for_task_id(qc_task_id, s3_bucket):
    print("get_token_for_task_id()")
    n = 0
    while n < 5:
        try:
            key = f"{s3_prefix}/qc_task_token/{qc_task_id}.json"
            return read_as_json(s3_bucket, key)
        except Exception as e:
            print(repr(e))
            n = n + 1
            time.sleep(2 * n)
    return None


def read_context(execution_id, bucket, s3_prefix):
    key = f"{s3_prefix}/executions/{execution_id}/user_input.json"
    print("read: s3://{}/{}".format(bucket, key))
    obj = s3.get_object(Bucket=bucket, Key=key)
    context = json.loads(obj['Body'].read())
    print(f"context={context}")
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
        key = f"{s3_prefix}/executions/{execution_id}/result/{task_id}/{name}"
        print(f"upload {f} -> {key}")
        s3.upload_file(f, bucket, key)
        keys.append(f"s3://{bucket}/{key}")
        del_local_file(f)
    return keys         


def handler(event, context):
    print(f"event={event}")
    aws_region = os.environ['AWS_REGION']
    # {'Records': [{'eventVersion': '2.1', 'eventSource': 'aws:s3', 'awsRegion': 'us-east-1', 'eventTime': '2021-11-29T05:17:52.234Z', 'eventName': 'ObjectCreated:Put', 'userIdentity': {'principalId': 'AWS:AROARFTQUWKOUWSYO5XRB:AWSServiceRoleForAmazonBraket'}, 'requestParameters': {'sourceIPAddress': '52.25.248.119'}, 'responseElements': {'x-amz-request-id': '1FQTNJ9HM86M7DMY', 'x-amz-id-2': 'UW1UEJKmwy6NcYRFnTafQSpD4sx05nAOxgs+YtEBH6ryx2MEGbXUj4nAW1ROIs6qtT2D12KCrcDMaKMnIDynCtLmwKAVQu8p'}, 's3': {'s3SchemaVersion': '1.0', 'configurationId': 'ZmNmMzBiZTktNTJiNi00YTllLTk1ODQtYjQyMWI1MzU2OTMw', 'bucket': {'name': 'amazon-braket-qcstack-main-080766874269-us-east-1', 'ownerIdentity': {'principalId': 'AKDTHGWL4N5KF'}, 'arn': 'arn:aws:s3:::amazon-braket-qcstack-main-080766874269-us-east-1'}, 'object': {'key': 'molecule-unfolding/qc_task_output/2fb927dc-32af-42a1-8517-b0872fa4e921/results.json', 'size': 16475, 'eTag': 'd86bf699fb617e1e03ea704695173f13', 'sequencer': '0061A462802499277F'}}}]}
    for rec in event['Records']:
        bucket = rec['s3']['bucket']['name']
        key = rec['s3']['object']['key']
        print(f"parsing file: s3://{bucket}/{key}")
        qc_task_id = key.split("/")[-2]
        print(f"qc_task_id: {qc_task_id}")
        prefix = "/".join(key.split("/")[:-2])

        task_info = get_token_for_task_id(qc_task_id, bucket)

        if not task_info:
            continue

        execution_id = task_info['execution_id']
        task_token = task_info['task_token']
        submit_result = task_info['submit_result']
       
        if task_already_done(execution_id, qc_task_id, bucket):
            print(f"qc_task_id={qc_task_id} already done")
            continue

        message = None
        try:
            model_info = submit_result['model_info']
            data_s3_path = model_info['data']
            raw_s3_path = model_info['raw']

            data_local_path = download_s3_file(data_s3_path)
            raw_local_path = download_s3_file(raw_s3_path)

            print(
                f"ResultParser(task_id={qc_task_id}, prefix={prefix}, data_path={data_local_path}, raw_path={raw_local_path}) ...")
            qa_process_result = ResultParser('dwave-qa',
                                             bucket=bucket,
                                             prefix=prefix,
                                             task_id=qc_task_id,
                                             data_path=data_local_path,
                                             raw_path=raw_local_path
                                             )

            local_time, task_time, total_time, access_time = qa_process_result.get_time()

            print(
                f"local_time={local_time}, task_time={task_time}, total_time={total_time}, access_time={access_time}")

   

            print("generate_optimize_pts()")
            timestamp = int(time.time())
            qa_atom_pos_data = qa_process_result.generate_optimize_pts()
            print(f"qa_atom_pos_data: {qa_atom_pos_data}")
            result_files = qa_process_result.save_mol_file(f"{timestamp}")  
            result_s3_files = upload_result_files(execution_id, qc_task_id, result_files, bucket)
            print(f"result_s3_files: {result_s3_files}")
            del_local_file(data_local_path)
            del_local_file(raw_local_path)


            model_param = submit_result['model_param']
            model_name = submit_result['model_name']
            mode_file_name = submit_result['mode_file_name']
            start_time = submit_result['start_time']
            experiment_name = submit_result['experiment_name']
            device_name = submit_result['device_name']
            #local_fit_time = submit_res['local_fit_time']

            time_info_json = json.dumps({
                                 "task_time": task_time,
                                 "total_time": total_time,
                                 "local_time": local_time,
                                 "access_time": access_time
                             })

            metrics_items = [execution_id,
                             "QC",
                             str(device_name),
                             model_param,
                             str(task_time),
                             time_info_json,
                             start_time,
                             experiment_name,
                             qc_task_id,
                             model_name,
                             mode_file_name,
                             s3_prefix,
                             datetime.datetime.utcnow().isoformat()
                             ]

            metrics = ",".join(metrics_items)
            print("metrics='{}'".format(metrics))
            metrics_key = f"{s3_prefix}/benchmark_metrics/{execution_id}-QC-{device_name}-{model_name}-{qc_task_id}.csv"
            string_to_s3(metrics, bucket, metrics_key)
            string_to_s3("Done", bucket,
                         key=f"{s3_prefix}/done_task/{execution_id}_{qc_task_id}")
            message = metrics_key
            success = True
        except Exception as e:
            string_to_s3(repr(e), bucket,
                         key=f"{s3_prefix}/err_task/{execution_id}_{qc_task_id}")
            print(repr(e))
            message = repr(e)
            success = False

           

        try:
            print(
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
            print(repr(e))
