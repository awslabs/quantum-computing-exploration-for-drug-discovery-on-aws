import boto3
import os
from collections import defaultdict
import json
import datetime
import copy

s3 = boto3.client('s3')
s3_prefix = "molecule-unfolding"

default_devices_arns = [
    'arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6',
    'arn:aws:braket:::device/qpu/d-wave/Advantage_system4'
]
default_model_params = {
    "M": [1, 2],
    "D": [4],
    "A": [300],
    "HQ": [200]  # hubo_qubo_val
}
default_hpc_resources = [
    # vcpu, memory
    (2, 2),
    # (4, 4),
    # (8, 8),
    (16, 16)
]


def string_to_s3(content, bucket, key):
    s3.put_object(
        Body=content.encode("utf-8"),
        Bucket=bucket,
        Key=key
    )


def read_user_input(execution_id, bucket, s3_prefix):
    key = f"{s3_prefix}/executions/{execution_id}/user_input.json"
    obj = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(obj['Body'].read())


def get_model_param_items(params_dict: dict):
    param_list = []
    for pname in ["M", "D", "A", "HQ"]:
        pvalues = [f"{pname}={v}" for v in params_dict.get(
            pname, default_model_params[pname])]
        param_list.append(pvalues)

    result = get_all_param_list(copy.deepcopy(param_list))
    print(f"get_param_items: {result}")
    return result


def get_all_param_list(param_list):
    first_l = None
    index_i = 0
    has_more_than_one = False
    for i in range(len(param_list)):
        l = param_list[i]
        if len(l) > 1:
            has_more_than_one = True

        if len(l) > 1 and first_l is None:
            first_l = l[0]
            param_list[i] = l[1:]
            index_i = i
    if not has_more_than_one:
        return ["&".join([ll[0] for ll in param_list])]
    else:
        param_list_copy = copy.deepcopy(param_list)
        param_list_copy[index_i] = [first_l]
        reslut_all = []
        result_list0 = get_all_param_list(param_list_copy)
        result_list1 = get_all_param_list(param_list)
        reslut_all.extend(result_list0)
        reslut_all.extend(result_list1)
        return reslut_all


def handler(event, context):
    print(f"event={event}")
    aws_region = os.environ['AWS_REGION']
    param_type = event['param_type']
    s3_bucket = event['s3_bucket']

    common_param = f"--aws_region,{aws_region},--s3-bucket,{s3_bucket}"

    if param_type == 'CHECK_INPUT':

        user_input = event['user_input']
        execution_id = event['execution_id']
        execution_id = execution_id.split(':')[-1]

        key = f"{s3_prefix}/executions/{execution_id}/user_input.json"
        string_to_s3(content=json.dumps({
            "user_input": user_input,
            "execution_id": execution_id,
            "aws_region": aws_region,
            "start_time": datetime.datetime.utcnow().isoformat()
        }), bucket=s3_bucket, key=key)
        return {
            "model_param": f"{common_param},--execution-id,{execution_id}".split(","),
            "execution_id": execution_id,
            "runMode": user_input.get('runMode', "ALL")
        }
    else:
        execution_id = event.get('execution_id', None)
        if execution_id:
            common_param = f"{common_param},--execution-id,{execution_id}"
            user_input = read_user_input(
                execution_id, bucket=s3_bucket, s3_prefix=s3_prefix)

            devices_arns = user_input.get('devicesArns', default_devices_arns)
            model_params = user_input.get('modelParams', default_model_params)
            hpc_resources = user_input.get(
                'hpcResources', default_hpc_resources)
        else:
            devices_arns = default_devices_arns
            model_params = default_model_params
            hpc_resources = default_model_params

    if param_type == 'QC_DEVICE_LIST':
        return {
            "devices_arns": devices_arns,
            "execution_id": execution_id
        }

    model_param_items = get_model_param_items(model_params)

    qc_task_params = defaultdict(list)
    qc_device_names = []
    for device_arn in devices_arns:
        device_name = device_arn.split("/").pop()
        qc_device_names.append(device_name)
        for param_item in model_param_items:
            param_item_name = str(param_item).replace(
                "&", '').replace("=", '')
            qc_task_params[device_arn].append({
                "params": f"--model-param,{param_item},--device-arn,{device_arn},{common_param}".split(","),
                "device_name": device_name,
                "task_name": f"{device_name}_{param_item_name}",
                "device_arn": device_arn})

    hpc_task_params = []
    for resource in hpc_resources:
        resource_name = f"Vcpu{resource[0]}_Mem{resource[1]}G"
        for param_item in model_param_items:
            param_item_name = str(param_item).replace(
                "&", '').replace("=", '')
            hpc_task_params.append({
                "params": f"--model-param,{param_item},--resource,{resource_name},{common_param}".split(","),
                "resource_name": resource_name,
                "task_name": f"{resource_name}_{param_item_name}",
                "vcpus": resource[0],
                "memory": resource[1] * 1024
            })

    if param_type == 'PARAMS_FOR_QC_DEVICE':
        device_arn = event['device_arn']
        print(f"device_arn={device_arn}")
        if device_arn not in devices_arns:
            raise ValueError(f"unknown device_arn: {device_arn}")

        print(qc_task_params)
        return {
            "qcTaskParams":  qc_task_params[device_arn],
            "execution_id": execution_id,
        }

    if param_type == 'PARAMS_FOR_HPC':
        return {
            "hpcTaskParams": hpc_task_params,
            "execution_id": execution_id
        }
